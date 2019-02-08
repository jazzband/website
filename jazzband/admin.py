from flask import redirect, url_for, request
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib import sqla
from flask_login import current_user

from .auth import current_user_is_roadie
from .db import postgres
from .members.models import User, EmailAddress
from .projects.models import (Project, ProjectCredential, ProjectUpload,
                              ProjectMembership)


class JazzbandModelView(sqla.ModelView):

    def is_accessible(self):
        return current_user_is_roadie()

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for('account.login', next=request.url))


class JazzbandAdminIndexView(AdminIndexView):

    @expose('/')
    def index(self):
        if not current_user.is_authenticated:
            return redirect(url_for('account.login', next=request.url))
        return super().index()


class UserAdmin(JazzbandModelView):
    column_searchable_list = ('login',)
    column_filters = (
        'is_member',
        'is_roadie',
        'is_banned',
        'is_restricted',
        'has_2fa',
        'joined_at',
        'left_at',
        'consented_at',
        'profile_consent',
        'org_consent',
        'cookies_consent',
        'age_consent',
    )
    inline_models = (EmailAddress, ProjectMembership)


class EmailAddressAdmin(JazzbandModelView):
    column_searchable_list = ('email',)
    column_filters = ('verified', 'primary')


class ProjectAdmin(JazzbandModelView):
    column_searchable_list = ('name', 'description')
    column_filters = ('is_active', 'created_at', 'updated_at', 'pushed_at')
    inline_models = (ProjectCredential, ProjectUpload, ProjectMembership)


class ProjectUploadAdmin(JazzbandModelView):
    column_searchable_list = ('filename', 'sha256_digest')
    column_filters = ('uploaded_at', 'released_at')


def init_app(app):
    admin = Admin(
        app,
        name='jazzband',
        template_mode='bootstrap3',
        index_view=JazzbandAdminIndexView(),
    )

    model_admins = [
        (User, UserAdmin),
        (EmailAddress, EmailAddressAdmin),
        (Project, ProjectAdmin),
        (ProjectMembership, JazzbandModelView),
        (ProjectUpload, ProjectUploadAdmin),
        (ProjectCredential, JazzbandModelView),
    ]

    for model_cls, admin_cls in model_admins:
        admin.add_view(admin_cls(model_cls, postgres.session))
