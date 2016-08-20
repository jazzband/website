from flask_login import current_user
from wtforms import Form, StringField, validators, ValidationError


class LeaveForm(Form):
    login = StringField('GitHub Login',
                        validators=[validators.input_required()])

    def validate_login(form, field):
        if field.data != current_user.login:
            raise ValidationError(
                "Sorry, but that GitHub login doesn't match our records.")
