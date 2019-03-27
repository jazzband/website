import logging
from datetime import datetime

import sentry_sdk
from flask import Blueprint, flash, redirect, session, url_for
from flask_login import (
    current_user, login_user, logout_user, login_required
)

from ..decorators import templated
from ..github import github
from ..members.models import User
from ..members.tasks import sync_email_addresses
from ..utils import get_redirect_target

from .forms import ConsentForm, LeaveForm

account = Blueprint('account', __name__, url_prefix='/account')

logger = logging.getLogger(__name__)


@account.app_template_global()
def default_url():
    return url_for('content.index')


@account.route('')
@login_required
@templated()
def dashboard():
    return {}


@account.route('/login')
def login():
    next_url = get_redirect_target('account.dashboard')
    if current_user.is_authenticated:
        return redirect(next_url)

    # Set the next URL in the session to be checked in the account callback
    session['next'] = next_url

    # default fallback is to initiate the GitHub auth workflow
    return github.authorize(scope=github.scope)


@account.route('/callback', methods=['GET', 'POST'])
@templated()
@github.authorized_handler
def callback(access_token):
    if not access_token:
        flash("Something went wrong during login. Please try again.")
        sentry_sdk.capture_message("Login attempt without access token")
        return redirect(default_url())

    form = ConsentForm(access_token=access_token)
    # first get the profile data for the user with the given access token
    user_data = github.get_user(access_token=form.access_token.data)

    # and see if the user is already in our database
    user = User.query.filter_by(id=user_data['id']).first()

    # on POST of the consent form
    if form.validate_on_submit():
        utc_now = datetime.utcnow()

        # if not, sync the data from GitHub with our database
        if user is None:
            results = User.sync([user_data])
            user, created = results[0]
            user.joined_at = utc_now

        # update a bunch of things
        if not user.consented_at:
            user.consented_at = utc_now
            user.profile_consent = True
            user.org_consent = True
            user.cookies_consent = True
            user.age_consent = True

    # we'll show the form either if there is no user yet,
    # or if the user hasn't given consent yet
    if user is None or not user.consented_at:
        return {'form': form}
    else:
        if user:
            user.access_token = access_token
            user.save()

        # fetch the current set of email addresses from GitHub
        sync_email_addresses(user.id, access_token)

        # remember the user_id for the next request
        login_user(user)
        # then redirect to the account dashboard
        flash("You've successfully logged in.")

        # Check for the next URL using the session first and then fallback
        next_url = (
            session.pop('next') or
            get_redirect_target('account.dashboard')
        )
        return redirect(next_url)


@account.route('/join')
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
        sync_email_addresses(current_user.id, current_user.access_token)
    has_verified_emails = current_user.has_verified_emails

    membership = None
    if has_verified_emails:
        membership = github.join_organization(current_user.login)
        if membership:
            flash("To join please accept the invitation from GitHub.")

    return {
        'next_url': 'https://github.com/jazzband/roadies/wiki/Welcome',
        'membership': membership,
        'org_id': github.org_id,
        'has_verified_emails': has_verified_emails,
    }


@account.route('/leave', methods=['GET', 'POST'])
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
            flash('Leaving the organization failed. '
                  'Please try again or open a ticket for the roadies.')
        else:
            current_user.left_at = datetime.utcnow()
            current_user.is_member = False
            current_user.save()
            logout_user()
            flash('You have been removed from the Jazzband GitHub '
                  'organization. See you soon!')
        return redirect(next_url)
    return {'form': form}


@account.route('/logout')
def logout():
    logout_user()
    flash("You've successfully logged out.")
    next_url = get_redirect_target()
    return redirect(next_url)
