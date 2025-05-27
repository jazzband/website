from datetime import datetime
import logging

from flask import Blueprint, flash, redirect, request, session, url_for
from flask_dance.consumer import oauth_authorized
from flask_login import current_user, login_required, login_user, logout_user
import sentry_sdk
from sqlalchemy.orm.exc import NoResultFound

from ..db import postgres as db
from ..decorators import templated
from ..exceptions import RateLimit
from ..members.models import User
from ..members.tasks import sync_email_addresses
from ..tasks import spinach
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


@account.route("/login")
def login():
    return redirect(url_for("github.login"))


@account.before_app_request
def redirect_to_consent():
    consent_url = url_for("account.consent")
    if (
        current_user.is_authenticated
        and not current_user.has_consented
        and not request.path.startswith("/static")
        and not request.path.startswith("/account")
    ):
        return redirect(consent_url)


@account.route("/consent", methods=["GET", "POST"])
@login_required
@templated()
def consent():
    # redirect to next url when current user has already consented
    if current_user.has_consented:
        return redirect(session.pop("next", default_url()))
    form = ConsentForm()

    if form.validate_on_submit():
        current_user.consented_at = datetime.utcnow()
        current_user.profile_consent = True
        current_user.org_consent = True
        current_user.cookies_consent = True
        current_user.age_consent = True
        current_user.save()
        next_url = session.pop("next", default_url())
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
            "Access to the GitHub API has been rate-limited, please try again later.",
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
    else:
        if oauth.token != token:
            oauth.token = token
            db.session.add(oauth)
            db.session.commit()

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

        # log in the new user
        login_user(user)

    # sync email addresses for the user
    spinach.schedule(sync_email_addresses, current_user.id)

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

    invited = False
    if has_verified_emails:
        invitation = github.join_organization(current_user.login)
        invited = invitation and invitation.status_code == 200
        if invited:
            flash(
                "To finish joining, please accept the invitation GitHub sent you via email!"
            )

    return {
        "invited": invited,
        "org_name": github.org_name,
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
        if response is None or response.status_code != 204:
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
