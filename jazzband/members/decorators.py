from flask import flash, redirect
from flask_login import current_user
import wrapt

from ..account.views import default_url


def member_required(next_url=None, message=None):
    if message is None:
        message = "Sorry but you're not a member of Jazzband at the moment."

    @wrapt.decorator
    def wrapper(wrapped, instance, args, kwargs):
        """
        If you decorate a view with this, it will ensure that the current user is
        a Jazzband member.

        :param func: The view function to decorate.
        :type func: function
        """
        nonlocal next_url
        if next_url is None:
            next_url = default_url()
        if (
            not current_user.is_member
            or current_user.is_banned
            or current_user.is_restricted
        ):
            flash(message)
            return redirect(next_url)
        return wrapped(*args, **kwargs)

    return wrapper
