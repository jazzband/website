from uuid import UUID, uuid4

from flask import redirect, request, session, url_for
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib import sqla
from flask_admin.model import typefmt
from flask_admin.model.form import InlineFormAdmin
from flask_login import current_user
from wtforms import StringField

from .account.models import OAuth
from .auth import current_user_is_roadie
from .db import postgres
from .members.models import EmailAddress, User
from .projects.models import (
    Project,
    ProjectCredential,
    ProjectMembership,
    ProjectUpload,
)


# Custom type formatter for UUID - displays as hex string
def uuid_formatter(view, value, name):
    return value.hex if value else ""


# Create custom type formatters dict including UUID
CUSTOM_FORMATTERS = dict(typefmt.BASE_FORMATTERS)
CUSTOM_FORMATTERS[UUID] = uuid_formatter


class JazzbandModelView(sqla.ModelView):
    # Apply UUID formatter to all model views
    column_type_formatters = CUSTOM_FORMATTERS

    def is_accessible(self):
        return current_user_is_roadie()

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        session["next"] = request.url
        return redirect(url_for("github.login"))


class JazzbandAdminIndexView(AdminIndexView):
    @expose("/")
    def index(self):
        if not current_user.is_authenticated:
            session["next"] = request.url
            return redirect(url_for("github.login"))
        return super().index()


class UserAdmin(JazzbandModelView):
    column_searchable_list = ("login",)
    column_filters = (
        "is_member",
        "is_roadie",
        "is_banned",
        "is_restricted",
        "has_2fa",
        "joined_at",
        "left_at",
        "consented_at",
        "profile_consent",
        "org_consent",
        "cookies_consent",
        "age_consent",
    )
    # Explicitly exclude problematic columns from forms
    form_excluded_columns = ["oauths", "email_addresses", "projects_memberships"]
    inline_models = [
        (OAuth, {"form_columns": ["id", "provider", "token"]}),
        EmailAddress,
        ProjectMembership,
    ]


class OAuthAdmin(JazzbandModelView):
    column_searchable_list = ("token", "user_id")
    column_filters = ("created_at", "provider")


class EmailAddressAdmin(JazzbandModelView):
    column_searchable_list = ("email",)
    column_filters = ("verified", "primary")


class ProjectCredentialInlineForm(InlineFormAdmin):
    """Custom inline form for ProjectCredential that displays key as read-only."""

    form_columns = ("id", "is_active", "key")

    # Add key as a read-only string field
    form_extra_fields = {"key": StringField("Key")}

    form_widget_args = {
        "key": {"readonly": True, "class": "form-control-plaintext"},
    }

    def on_model_change(self, form, model):
        """Ensure key is generated for new credentials."""
        if not model.key:
            model.key = uuid4()

    def postprocess_form(self, form_class):
        """Post-process the inline form to populate key field."""
        # The key field will be populated from the model data automatically
        return form_class


class ProjectAdmin(JazzbandModelView):
    column_searchable_list = ("name", "description")
    column_filters = ("is_active", "created_at", "updated_at", "pushed_at")

    inline_models = [
        ProjectCredentialInlineForm(ProjectCredential),
        ProjectUpload,
        ProjectMembership,
    ]


class ProjectUploadAdmin(JazzbandModelView):
    column_searchable_list = ("filename", "sha256_digest")
    column_filters = ("uploaded_at", "released_at")


class ProjectMembershipAdmin(JazzbandModelView):
    column_filters = ("is_lead", "user_id", "project_id", "joined_at")
    column_searchable_list = ("project_id", "user_id")


class ProjectCredentialAdmin(JazzbandModelView):
    column_list = ("id", "project", "is_active", "key")
    column_filters = ("is_active", "project_id")
    form_columns = ("project", "is_active", "key")

    # Enable detail view so users can see the full key
    can_view_details = True
    column_details_list = ("id", "project", "is_active", "key")

    # Add key as a read-only string field in forms
    form_extra_fields = {
        "key": StringField("Key", description="Auto-generated (read-only)")
    }

    form_widget_args = {
        "key": {"readonly": True, "class": "form-control-plaintext"},
    }

    def on_model_change(self, form, model, is_created):
        """Ensure key is generated for new credentials."""
        if is_created and not model.key:
            model.key = uuid4()


def init_app(app):
    admin = Admin(
        app,
        name="jazzband",
        index_view=JazzbandAdminIndexView(),
    )

    model_admins = [
        (User, UserAdmin),
        (OAuth, OAuthAdmin),
        (EmailAddress, EmailAddressAdmin),
        (Project, ProjectAdmin),
        (ProjectMembership, ProjectMembershipAdmin),
        (ProjectUpload, ProjectUploadAdmin),
        (ProjectCredential, ProjectCredentialAdmin),
    ]

    for model_cls, admin_cls in model_admins:
        admin.add_view(admin_cls(model_cls, postgres.session))
