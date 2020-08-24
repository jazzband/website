from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import ValidationError, validators
from wtforms.fields import BooleanField, StringField

CONSENT_ERROR_MESSAGE = "Your consent is required to continue."


class ConsentForm(FlaskForm):
    profile = BooleanField(
        "I consent to fetching, processing and storing my profile "
        "data which is fetched from the GitHub API.",
        validators=[validators.DataRequired(CONSENT_ERROR_MESSAGE)],
    )
    org = BooleanField(
        "I consent to fetching, processing and storing my GitHub "
        "organization membership data which is fetched from the "
        "GitHub API.",
        validators=[validators.DataRequired(CONSENT_ERROR_MESSAGE)],
    )
    cookies = BooleanField(
        "I consent to using browser cookies for identifying me for "
        "account features such as logging in and content personalizations "
        "such as rendering my account dashboard.",
        validators=[validators.DataRequired(CONSENT_ERROR_MESSAGE)],
    )
    age = BooleanField(
        "I'm at least 16 years old or – if not – have permission by a "
        "parent (or legal guardian) to proceed.",
        validators=[validators.DataRequired(CONSENT_ERROR_MESSAGE)],
    )


class LeaveForm(FlaskForm):
    login = StringField("Your GitHub Login", validators=[validators.DataRequired()])

    def validate_login(self, field):
        if field.data != current_user.login:
            raise ValidationError(
                "Sorry, but that GitHub login doesn't match our records."
            )
