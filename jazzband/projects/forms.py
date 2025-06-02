import re

from flask_login import current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from packaging import version
from wtforms import StringField, SubmitField, ValidationError, validators


_project_name_re = re.compile(
    r"^([A-Z0-9]|[A-Z0-9][A-Z0-9._-]*[A-Z0-9])$", re.IGNORECASE
)

UPLOAD_EXTENSIONS = [
    "exe",
    "tar.gz",
    "bz2",
    "rpm",
    "deb",
    "zip",
    "tgz",
    "egg",
    "dmg",
    "msi",
    "whl",
]


def _validate_pep440_version(form, field):
    parsed = version.parse(field.data)

    # Check that this version is a valid PEP 440 version at all.
    if not isinstance(parsed, version.Version):
        raise validators.ValidationError(
            "Must start and end with a letter or numeral and contain only "
            "ascii numeric and '.', '_' and '-'."
        )

    # Check that this version does not have a PEP 440 local segment attached
    # to it.
    if parsed.local is not None:
        raise validators.ValidationError("Cannot use PEP 440 local versions.")


class UploadForm(FlaskForm):
    # Identity Project and Release
    name = StringField(
        validators=[
            validators.DataRequired(),
            validators.Regexp(
                _project_name_re,
                re.IGNORECASE,
                message=(
                    "Must start and end with a letter or numeral and contain "
                    "only ascii numeric and '.', '_' and '-'."
                ),
            ),
        ]
    )
    version = StringField(
        validators=[
            validators.DataRequired(),
            validators.Regexp(
                r"^(?!\s).*(?<!\s)$",
                message="Cannot have leading or trailing whitespace.",
            ),
            _validate_pep440_version,
        ]
    )

    content = FileField(
        validators=[
            FileRequired("Upload payload does not have a file."),
            FileAllowed(UPLOAD_EXTENSIONS, "Invalid file extension."),
        ]
    )

    gpg_signature = FileField(
        validators=[
            validators.Optional(),
            FileAllowed(["asc"], "Invalid file extension."),
        ]
    )

    md5_digest = StringField(validators=[validators.Optional()])

    sha256_digest = StringField(
        validators=[
            validators.Optional(),
            validators.Regexp(
                r"^[A-F0-9]{64}$",
                re.IGNORECASE,
                message="Must be a valid, hex encoded, SHA256 message digest.",
            ),
        ]
    )

    blake2_256_digest = StringField(
        validators=[
            validators.Optional(),
            validators.Regexp(
                r"^[A-F0-9]{64}$",
                re.IGNORECASE,
                message="Must be a valid, hex encoded, blake2 message digest.",
            ),
        ]
    )

    def validate_content(form, field):
        if field.data and ("/" in field.data or "\\" in field.data):
            raise ValidationError("Cannot upload a file with '/' or '\\' in the name.")


class ProjectNameForm(FlaskForm):
    project_name = StringField("Project name", validators=[validators.DataRequired()])

    def __init__(self, project_name, *args, **kwargs):
        self._project_name = project_name
        super().__init__(*args, **kwargs)

    def validate_project_name(self, field):
        if field.data != self._project_name:
            raise ValidationError("Sorry, but the entered project name doesn't match.")


class TwoFactorAuthValidation:
    submit = SubmitField()

    def validate_submit(self, field):
        if not current_user.has_2fa:
            raise ValidationError(
                "Sorry, but to release the upload you need to have "
                "Two Factor Auth (2FA) enabled on GitHub."
            )


class ReleaseForm(TwoFactorAuthValidation, ProjectNameForm):
    submit = SubmitField("Release")

    def __init__(self, *args, **kwargs):
        self.global_errors = []
        super().__init__(*args, **kwargs)

    def add_global_error(self, *messages):
        self.global_errors.extend(messages)


class BulkReleaseForm(TwoFactorAuthValidation, ProjectNameForm):
    submit = SubmitField("Bulk Release")

    def __init__(self, *args, **kwargs):
        self.global_errors = []
        super().__init__(*args, **kwargs)

    def add_global_error(self, *messages):
        self.global_errors.extend(messages)


class DeleteForm(TwoFactorAuthValidation, ProjectNameForm):
    submit = SubmitField("Delete")
