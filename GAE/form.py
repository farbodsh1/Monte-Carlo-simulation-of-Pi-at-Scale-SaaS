from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField, SelectField
from wtforms.validators import DataRequired, NumberRange


class FirstForm(FlaskForm):
    # accounting for warm-up
    service_input = SelectField(u'Service:', choices=[('lambda', 'AWS - Lambda'), ('ec2', 'AWS - EC2')])
    r_input = IntegerField('R:', render_kw={"placeholder": "Parallel Resources"}, validators=[DataRequired(message="Only integers between 1 and 10."), NumberRange(min=1, max=10, message="Only integers between 1 and 10.")])
    continue_btn = SubmitField("Continue")

class SecondForm(FlaskForm):    
    d_input = IntegerField('D:', render_kw={"placeholder": "Digits Precision"}, validators=[DataRequired(message="Only integers between 1 and 10."), NumberRange(min=1, max=10, message="Only integers between 1 and 10.")])
    s_input = IntegerField('S:', render_kw={"placeholder": "Shots"}, validators=[DataRequired(message="Only integers between 1,000 and 10,000,000."), NumberRange(min=1_000, max=10_000_000, message="Only integers between 1,000 and 10,000,000.")])
    q_input = IntegerField('Q:', render_kw={"placeholder": "Reporting Rate"}, validators=[DataRequired(message="Only integers larger than or equal to 1000."), NumberRange(min=1_000, message="Only integers larger than or equal to 1000.")])
    submit = SubmitField("Calculate")

class ThirdForm(FlaskForm):    
    submit_yes = SubmitField("Yes")
    submit_no = SubmitField("No")
