from flask import redirect, url_for, request
from flask_admin import Admin
from flask_admin.contrib import sqla
from flask.ext.login import current_user


admin = Admin(name='jazzband', template_mode='bootstrap3')


class JazzbandModelView(sqla.ModelView):

    def is_accessible(self):
        if not current_user.is_authenticated:
            return False
        return bool(current_user.is_roadie)

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for('account.login', next=request.url))
