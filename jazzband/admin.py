from flask import redirect, url_for, request
from flask_admin import Admin
from flask_admin.contrib import sqla
from .auth import current_user_is_roadie


admin = Admin(name='jazzband', template_mode='bootstrap3')


class JazzbandModelView(sqla.ModelView):

    def is_accessible(self):
        return current_user_is_roadie()

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for('account.login', next=request.url))
