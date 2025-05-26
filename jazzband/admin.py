from flask import redirect, request, session, url_for
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib import sqla
from flask_login import current_user

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


class JazzbandModelView(sqla.ModelView):
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
        (OAuth, {"form_columns": ["provider", "token"]}),
        EmailAddress,
        ProjectMembership,
    ]


class OAuthAdmin(JazzbandModelView):
    column_searchable_list = ("token", "user_id")
    column_filters = ("created_at", "provider")


class EmailAddressAdmin(JazzbandModelView):
    column_searchable_list = ("email",)
    column_filters = ("verified", "primary")


class ProjectAdmin(JazzbandModelView):
    column_searchable_list = ("name", "description")
    column_filters = ("is_active", "created_at", "updated_at", "pushed_at")

    inline_models = [ProjectCredential, ProjectUpload, ProjectMembership]


class ProjectUploadAdmin(JazzbandModelView):
    column_searchable_list = ("filename", "sha256_digest")
    column_filters = ("uploaded_at", "released_at")


class ProjectMembershipAdmin(JazzbandModelView):
    column_filters = ("is_lead", "user_id", "project_id", "joined_at")
    column_searchable_list = ("project_id", "user_id")


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
        (ProjectCredential, JazzbandModelView),
    ]

    for model_cls, admin_cls in model_admins:
        admin.add_view(admin_cls(model_cls, postgres.session))
