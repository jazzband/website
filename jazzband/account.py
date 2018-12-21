from datetime import datetime

from flask import Blueprint, redirect, session, url_for, flash
from flask_login import (LoginManager, current_user,
                         login_user, logout_user, login_required)
from flask_wtf import FlaskForm
from wtforms import validators, ValidationError
from wtforms.fields import BooleanField, HiddenField, StringField

from .decorators import templated
from .github import github
from .members.jobs import sync_user_email_addresses
from .members.models import db, User
from .utils import get_redirect_target

login_manager = LoginManager()
login_manager.login_view = 'account.login'
account = Blueprint('account', __name__, url_prefix='/account')


class LeaveForm(FlaskForm):
    login = StringField(
        'Your GitHub Login',
        validators=[
            validators.DataRequired(),
        ]
    )

    def validate_login(self, field):
        if field.data != current_user.login:
            raise ValidationError(
                "Sorry, but that GitHub login doesn't match our records.")


CONSENT_ERROR_MESSAGE = 'Your consent is required to continue.'


class ConsentForm(FlaskForm):
    access_token = HiddenField(
        'GitHub access token',
        validators=[
            validators.DataRequired(),
        ],
    )
    profile = BooleanField(
        'I consent to fetching, processing and storing my profile '
        'data which is fetched from the GitHub API.',
        validators=[
            validators.DataRequired(CONSENT_ERROR_MESSAGE),
        ],
    )
    org = BooleanField(
        'I consent to fetching, processing and storing my GitHub '
        'organiztion membership data which is fetched from the '
        'GitHub API.',
        validators=[
            validators.DataRequired(CONSENT_ERROR_MESSAGE),
        ],
    )
    cookies = BooleanField(
        'I consent to using browser cookies for identifying me for '
        'account features such as logging in and content personalizations '
        'such as rendering my account dashboard.',
        validators=[
            validators.DataRequired(CONSENT_ERROR_MESSAGE),
        ],
    )
    age = BooleanField(
        'I\'m at least 16 years old or – if not – have permission by a '
        'parent (or legal guardian) to proceed.',
        validators=[
            validators.DataRequired(CONSENT_ERROR_MESSAGE),
        ],
    )


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@account.app_template_global()
def default_url():
    return url_for('content.index')


@github.access_token_getter
def token_getter():
    if current_user.is_authenticated:
        return current_user.access_token


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
    session['next_url'] = next_url

    # default fallback is to initiate the GitHub auth workflow
    return github.authorize(scope=github.scope)


@account.route('/callback', methods=['GET', 'POST'])
@templated()
@github.authorized_handler
def callback(access_token):
    form = ConsentForm(access_token=access_token)
    # first get the profile data for the user with the given access token
    user_data = github.get_user(access_token=access_token or form.access_token.data)

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
        user.access_token = form.access_token.data

        if not user.consented_at:
            user.consented_at = utc_now
            user.profile_consent = True
            user.org_consent = True
            user.cookies_consent = True
            user.age_consent = True
        db.session.commit()

    # we'll show the form either if there is no user yet,
    # or if the user hasn't given consent yet
    if user is None or not user.consented_at:
        return {'form': form}
    else:
        # fetch the current set of email addresses from GitHub
        sync_user_email_addresses.queue(user.id)

        # remember the user_id for the next request
        login_user(user)
        # then redirect to the account dashboard
        flash("You've successfully logged in.")

        # Check for the next URL using the session first and then fallback
        next_url = (
            session.get('next_url') or
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

    has_verified_emails = current_user.has_verified_emails
    # in case the user doesn't have verified emails, let's check again
    # the async task may not have run yet
    if not has_verified_emails:
        sync_user_email_addresses(current_user.id)
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
            db.session.commit()
            logout_user()
            flash('You have been removed from the Jazzband GitHub '
                  'organization. See you soon!')
        return redirect(next_url)
    return {'form': form}


@account.route('/logout')
def logout():
    logout_user()
    flash("You've successfully logged out.")
    return redirect(default_url())
