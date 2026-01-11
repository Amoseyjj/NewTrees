from wtforms import Form, StringField, TextAreaField, validators
from wtforms.fields import EmailField, TelField


class CreateContactForm(Form):
    first_name = StringField('First Name', [validators.Length(min=1, max=150), validators.DataRequired()])
    last_name = StringField('Last Name', [validators.Length(min=1, max=150), validators.DataRequired()])
    phone_number = TelField('Phone Number',
                            [validators.Length(min=8, max=8),
                                validators.DataRequired()])
    email = EmailField('Email', [validators.Email(), validators.DataRequired()])
    message = TextAreaField('Message', [validators.Length(min=1), validators.DataRequired()])
