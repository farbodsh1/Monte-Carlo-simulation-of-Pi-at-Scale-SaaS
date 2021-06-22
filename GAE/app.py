# standard libraries
import json
import math
import time
from datetime import datetime, timedelta
import concurrent.futures

# third-party
import pandas as pd
from flask import Flask, render_template, url_for, request, redirect, session, flash

# local
from form import *
from params import Params
from visuals import plot_pi_linechart, plot_table
from utils import *


app = Flask(__name__)
app.config['SECRET_KEY'] = Params.APP_PI_SECRET_KEY
app.permanent_session_lifetime = timedelta(days=Params.APP_SESSION_LIFETIME_DAYS)

@app.route("/", methods=['GET', 'POST'])
def home():
    form = FirstForm()
    if form.validate_on_submit():
        # user inputs
        messages = {
            "service":request.form["service_input"],
            "R":int(request.form["r_input"])
        }
        if messages["service"] == "ec2":
            running_ec2_ips = aws_get_running_ips()
            required_additional_ec2s = messages["R"] - len(running_ec2_ips)
            if required_additional_ec2s > 0:
                # warm up additional required EC2s
                aws_create_ec2s(n_instances_to_start=required_additional_ec2s)
                time.sleep(Params.APP_SHORT_WAIT)
        return redirect(url_for("calculation", messages=json.dumps(messages)))
    return render_template('home.html', form=form, title="Home")


@app.route("/calculation", methods=['GET', 'POST'])
def calculation():
    form = SecondForm()
    messages = json.loads(request.args['messages']) # existing user inputs (dict)
    if form.validate_on_submit():
        # user inputs (more fields)
        messages.update({
            "D":int(request.form["d_input"]),
            "S":int(request.form["s_input"]),
            "Q":int(request.form["q_input"]),
        })
        subshots = messages["S"] // messages["R"]

        # sub-calculations
        res = []
        calculated_pi = 0
        retries = 0
        duration = 0
        # iterate until PI precision meets requirements or exhausted all retries
        while (round(math.pi, messages["D"] - 1) != round(calculated_pi, messages["D"] - 1)) and (retries < Params.MAX_PI_CALC_RETRIES):
            retries += 1
            if messages["service"] == "lambda":
                # use AWS Lambda
                configs = generate_aws_lambda_configs(subshots=subshots, report_rate=messages["Q"], resources_count=messages["R"])
            elif messages["service"] == "ec2":
                # use AWS EC2
                running_ec2_ips = list(aws_get_running_ips().values())
                if len(running_ec2_ips) < messages["R"]:
                    flash("Not enough EC2 resources. Please try again.", "danger")
                    return redirect(url_for("home"))
                configs = generate_aws_ec2_configs(subshots=subshots, report_rate=messages["Q"], resources_count=messages["R"], ec2_public_ips=running_ec2_ips)
            with concurrent.futures.ThreadPoolExecutor(max_workers=messages["R"]) as ex:
                temp_res = list(ex.map(call_api, configs))
                for l in temp_res:
                    res.extend(l[0]) # compute result
                    duration += l[1] # sub-duration
            df = pd.DataFrame(res)
            df["cumulative_in_circle"] = df["in_circle"].cumsum()
            df["cumulative_shots"] = df["shots"].cumsum()
            df["intermediate_pi"] = df["cumulative_in_circle"] / df["cumulative_shots"] * 4
            calculated_pi = float(df.iloc[-1]["intermediate_pi"])
        df = df.reset_index().rename({"index":"#"}, axis=1)
        df["#"] += 1

        # final Pi & duration summarised
        final_result = {
            "Timestamp":datetime.now().strftime("%Y-%m-%d %T"),
            "Final Estimated Pi":round(calculated_pi, Params.ROUND_VALUES_DP),
            "Total Duration (Seconds)":round(duration, Params.ROUND_VALUES_DP),
            "Total Cost ($)":round(estimate_compute_cost(service=messages["service"], duration_sec=duration), Params.ROUND_VALUES_DP), 
            "Service":messages["service"],
            "S":messages["S"],
            "Q":messages["Q"],
            "R":messages["R"],
            "D":messages["D"],
        }

        # save recent request & response in History as session
        session.permanent = True
        if "history" not in session:
            session["history"] = [final_result]
        else:
            session["history"] = session["history"] + [final_result]
        final_df = pd.DataFrame([final_result]).T.reset_index()

        # render following
        plot = plot_pi_linechart(df)
        table = plot_table(df, title="Result Table", col_widths=[70, 400, 100, 100, 200, 200, 200])
        final_table = plot_table(final_df, title="Final Table", plot_header=False)
        return render_template('calculation.html', form=form, plot=plot, table=table, final_table=final_table)
    return render_template('calculation.html', form=form, title="Calculation")


@app.route("/history")
def history():
    history = session.get("history", None)
    if history:
        history = pd.DataFrame(history)
        history = history[["Timestamp", "Service", "S", "Q", "R", "D", "Final Estimated Pi", "Total Duration (Seconds)", "Total Cost ($)"]]
        history = plot_table(history)
    return render_template('history.html', title="History", history=history)


@app.route("/delete_history", methods=['GET', 'POST'])
def delete_history():
    form = ThirdForm()
    if form.validate_on_submit():
        if request.form.get("submit_no"):
            flash("Did not delete history.", "info")
            return redirect(url_for("home"))
        if request.form.get("submit_yes"):
            # clear history in session
            session.clear()
            flash("Deleted history.", "info")
            return redirect(url_for("home"))
    return render_template('delete_history.html', form=form, title="Delete History")


@app.route("/terminate", methods=['GET', 'POST'])
def terminate():
    form = ThirdForm()
    if form.validate_on_submit():
        if request.form.get("submit_no"):
            flash("Did not terminate resources.", "info")
            return redirect(url_for("home"))
        if request.form.get("submit_yes"):
            # terminate EC2 instances
            aws_terminate_instances()
            flash("Terminated all resources.", "info")
            return redirect(url_for("home"))
    return render_template('terminate.html', form=form, title="Terminate Resources")


# HTTP error handlers
@app.errorhandler(404)
def page_not_found(err):
    flash(f"{err}", "danger")
    return redirect(url_for('home'))


@app.errorhandler(500)
def page_not_found(err):
    flash(f"Internal Server Error! Please try again.", "danger")
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(host=Params.APP_DEV_HOST, port=Params.APP_DEV_PORT, debug=Params.APP_DEV_DEBUG)
