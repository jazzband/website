import logging
from datetime import datetime

import sentry_sdk
from flask import flash, redirect, request, session, url_for, Blueprint
from flask_login import current_user, login_user, logout_user, login_required
from flask_dance.consumer import oauth_before_login, oauth_authorized
from sqlalchemy.orm.exc import NoResultFound

from ..db import postgres as db
from ..decorators import templated
from ..exceptions import RateLimit
from ..members.models import User
from ..members.tasks import sync_email_addresses
from ..utils import get_redirect_target

from . import github
from .blueprint import GitHubBlueprint
from .forms import ConsentForm, LeaveForm
from .models import OAuth

account = Blueprint("account", __name__, url_prefix="/account")

github_bp = GitHubBlueprint(
    "github", __name__, url_prefix="/account", redirect_to="account.consent"
)

logger = logging.getLogger(__name__)


@account.app_template_global()
def default_url():
    return url_for("content.index")


@account.route("")
@login_required
@templated()
def dashboard():
    return {}


@oauth_before_login.connect
def before_login(blueprint, url):
    session["next_url"] = get_redirect_target("account.dashboard")


@account.before_app_request
def redirect_to_consent():
    consent_url = url_for("account.consent")
    if (
        current_user.is_authenticated
        and not current_user.has_consented
        and not request.path.startswith("/account")
    ):
        return redirect(consent_url)


@account.route("/consent", methods=["GET", "POST"])
@login_required
@templated()
def consent():
    # redirect to next url when current user has already consented
    if current_user.has_consented:
        return redirect(session.pop("next_url", default_url()))
    form = ConsentForm()

    if form.validate_on_submit():
        current_user.consented_at = datetime.utcnow()
        current_user.profile_consent = True
        current_user.org_consent = True
        current_user.cookies_consent = True
        current_user.age_consent = True
        current_user.save()
        next_url = session.pop("next_url", default_url())
        return redirect(next_url)

    return {"form": form}


def fail_callback():
    flash("Something went wrong during login. Please try again.", category="error")


@oauth_authorized.connect
def callback(blueprint, token):
    if not token:
        fail_callback()
        sentry_sdk.capture_message("Login attempt without access token")
        return False

    if "error_reason" in token:
        fail_callback()
        reason = request.args["error_reason"]
        error = request.args["error_description"]
        sentry_sdk.capture_message(f"Access denied. Reason {reason} error={error}")
        return False

    # first get the profile data for the user
    try:
        user_response = blueprint.session.get("/user")
    except RateLimit:
        flash(
            "Access to the GitHub API has been rate-limited, "
            "please try again later.",
            category="error",
        )
        return False

    # something happened while fetching the user profile from GitHub
    if not user_response.ok:
        flash("Failed to fetch user info from GitHub.", category="error")
        return False

    user_data = user_response.json()
    github_user_id = str(user_data["id"])

    # Find this OAuth token in the database, or create it
    query = OAuth.query.filter_by(
        provider=blueprint.name,
        # we're using the user foreignkey's id here
        # since we assume user.id == githubuser.id
        user_id=github_user_id,
    )
    try:
        oauth = query.one()
    except NoResultFound:
        oauth = OAuth(provider=blueprint.name, user_id=github_user_id, token=token)

    if oauth.user:
        # If there is a user assigned to the OAuth token already we log them in
        login_user(oauth.user)
    else:
        # or else we create/update a user object and assign it to the OAuth
        # token object
        utc_now = datetime.utcnow()
        results = User.sync([user_data])
        user, created = results[0]
        # store the joined date when the user was created
        if created:
            user.joined_at = utc_now
        # assign the new user with the OAuth token
        oauth.user = user
        db.session.add_all([user, oauth])
        db.session.commit()

        # sync email addresses for the user
        sync_email_addresses(user.id)

        # log in the new user
        login_user(user)

    flash("You've successfully logged in.")
    # Return False here to prevent Flask-Dance creating an own instance
    # of the OAuth token
    return False


@account.route("/join")
@login_required
@templated()
def join():
    next_url = default_url()

    if current_user.is_banned:
        flash("You've been banned from Jazzband")
        logout_user(current_user)
        return redirect(next_url)
    elif current_user.is_restricted:
        flash("Your account is currently restricted")
        logout_user(current_user)
        return redirect(next_url)
    elif current_user.is_member:
        flash("You're already a member of Jazzband")
        return redirect(next_url)

    if not current_user.has_verified_emails:
        sync_email_addresses(current_user.id)
    has_verified_emails = current_user.has_verified_emails

    membership = None
    if has_verified_emails:
        membership = github.join_organization(current_user.login)
        if membership:
            flash("To join please accept the invitation from GitHub.")

    return {
        "next_url": "https://github.com/jazzband/roadies/wiki/Welcome",
        "membership": membership,
        "org_id": github.org_id,
        "has_verified_emails": has_verified_emails,
    }


@account.route("/leave", methods=["GET", "POST"])
@login_required
@templated()
def leave():
    next_url = default_url()
    if not current_user.is_member:
        flash("You're not a member of Jazzband at the moment.")
        return redirect(next_url)

    form = LeaveForm()
    if form.validate_on_submit():
        response = github.leave_organization(current_user.login)
        if response is None:
            flash(
                "Leaving the organization failed. "
                "Please try again or open a ticket for the roadies."
            )
        else:
            current_user.left_at = datetime.utcnow()
            current_user.is_member = False
            current_user.save()
            logout_user()
            flash(
                "You have been removed from the Jazzband GitHub "
                "organization. See you soon!"
            )
        return redirect(next_url)
    return {"form": form}


@account.route("/logout")
def logout():
    logout_user()
    flash("You've successfully logged out.")
    next_url = get_redirect_target()
    return redirect(next_url)
