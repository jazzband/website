import logging

from flask import current_app, flash
from flask_dance.consumer import OAuth2ConsumerBlueprint, oauth_error
from flask_dance.consumer.requests import BaseOAuth2Session, OAuth2Session
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from flask_login import current_user, login_user
from sentry_sdk import capture_message, configure_scope
from urlobject import URLObject
from werkzeug.utils import cached_property

from ..cache import cache
from ..db import postgres as db
from ..exceptions import RateLimit
from .models import OAuth

logger = logging.getLogger(__name__)


@oauth_error.connect
def github_error(blueprint, error, error_description=None, error_uri=None):
    """A GitHub API error handler that pushes the error to Sentry
    and shows a flash message to the user.
    """
    if error:
        with configure_scope() as scope:
            scope.set_extra("error_description", error_description)
            scope.set_extra("error_uri", error_uri)
            capture_message(f"Error during OAUTH found: {error}")
        flash(
            f"OAuth error from Github ({error}): {error_description}", category="error"
        )


class GitHubSessionMixin:
    """A requests session mixin for GitHub that implements currently:

    - rate limit handling (by raising an exception when it happens)
    - pagination by the additional all_pages parameter
    """

    def request(self, method, url, data=None, headers=None, all_pages=False, **kwargs):
        response = super().request(
            method=method, url=url, data=data, headers=headers, **kwargs
        )

        if response.status_code == 403:
            ratelimit_remaining = response.headers.get("X-RateLimit-Remaining")
            if ratelimit_remaining:
                try:
                    if int(ratelimit_remaining) < 1:
                        raise RateLimit(response=response)
                except ValueError:
                    pass

        if all_pages:
            result = response.json()
            while response.links.get("next"):
                url = response.links["next"]["url"]
                response = super().request(
                    method=method, url=url, data=data, headers=headers, **kwargs
                )
                body = response.json()
                if isinstance(body, list):
                    result += body
                elif isinstance(body, dict) and "items" in body:
                    result["items"] += body["items"]
            return result
        else:
            return response


class GitHubSession(GitHubSessionMixin, OAuth2Session):
    """A custom GitHub session that implements a bunch of GitHub
    API specific functionality (e.g. pagination and rate limit handling)
    """


class AdminGitHubSession(GitHubSessionMixin, BaseOAuth2Session):
    """A custom GitHub session class that uses the blueprint's
    admin access token.
    """

    def __init__(self, blueprint=None, base_url=None, **kwargs):
        # Create token from blueprint admin access token
        token = {"access_token": blueprint.admin_access_token}
        # Pass token through kwargs to avoid star-arg unpacking issues
        kwargs["token"] = token
        # Initialize parent class without using *args
        super().__init__(**kwargs)
        self.blueprint = blueprint
        self.base_url = URLObject(base_url)

    def request(self, method, url, data=None, headers=None, **kwargs):
        if self.base_url:
            url = self.base_url.relative(url)

        # Add client_id and client_secret to kwargs to avoid star-arg unpacking after keyword args
        kwargs.update(
            {
                "method": method,
                "url": url,
                "data": data,
                "headers": headers,
                "client_id": self.blueprint.client_id,
                "client_secret": self.blueprint.client_secret,
            }
        )
        return super().request(**kwargs)


class GitHubBlueprint(OAuth2ConsumerBlueprint):
    """
    A custom OAuth2 blueprint that implements some of our
    specific GitHub API functions.
    """

    def __init__(self, *args, **kwargs):
        # Define default keyword arguments for GitHub OAuth blueprint
        default_kwargs = {
            "base_url": "https://api.github.com/",
            "authorization_url": "https://github.com/login/oauth/authorize",
            "token_url": "https://github.com/login/oauth/access_token",
            "session_class": GitHubSession,
            "storage": SQLAlchemyStorage(
                OAuth, db.session, user=current_user, user_required=False, cache=cache
            ),
        }
        # Update defaults with any provided kwargs
        default_kwargs.update(kwargs)
        # Call parent init with args and merged kwargs
        super().__init__(*args, **default_kwargs)
        self.from_config.update(
            {
                "client_id": "GITHUB_OAUTH_CLIENT_ID",
                "client_secret": "GITHUB_OAUTH_CLIENT_SECRET",
                "scope": "GITHUB_SCOPE",
                "members_team_slug": "GITHUB_MEMBERS_TEAM_SLUG",
                "roadies_team_slug": "GITHUB_ROADIES_TEAM_SLUG",
                "admin_access_token": "GITHUB_ADMIN_TOKEN",
                "org_name": "GITHUB_ORG_NAME",
            }
        )

    def make_setup_state(self, app, options, first_registration=False):
        # load config when the blueprint is registered
        if first_registration:
            with app.app_context():
                self.load_config()
        return super().make_setup_state(
            app, options, first_registration=first_registration
        )

    @cached_property
    def admin_session(self):
        # FIXME investigate why config is not loading on cli invocation
        self.load_config()

        "This is a custom session using the organization's admin permissions."
        return AdminGitHubSession(
            client_id=self._client_id,
            client=self.client,
            auto_refresh_url=self.auto_refresh_url,
            auto_refresh_kwargs=self.auto_refresh_kwargs,
            scope=self.scope,
            state=self.state,
            blueprint=self,
            base_url=self.base_url,
            **self.kwargs,
        )

    def join_organization(self, user_login):
        """
        Adds the GitHub user with the given login to the members team.
        """
        return self.join_team(self.members_team_slug, user_login)

    def leave_organization(self, user_login):
        """
        Remove the GitHub user with the given login from the org.

        https://docs.github.com/en/rest/reference/orgs#remove-an-organization-member
        """
        return self.admin_session.delete(
            f"orgs/{self.org_name}/memberships/{user_login}"
        )

    def get_project_team(self, slug):
        """
        Get the information about the team with the given name.
        """
        return self.admin_session.get(f"orgs/{self.org_name}/teams/{slug}")

    def get_members_team_id(self):
        """
        Fetches the GitHub team id of the Members team.
        """
        member_team_response = self.admin_session.get(
            f"orgs/{self.org_name}/teams/{self.members_team_slug}"
        )
        member_team_response.raise_for_status()
        member_team_data = member_team_response.json()
        return member_team_data.get("id")

    def create_project_team(self, name):
        """
        Create a project team in the members team with the given name.

        Docs: https://docs.github.com/en/rest/reference/teams#create-a-team
        """
        members_team_id = self.get_members_team_id()
        if not members_team_id:
            logger.error("Couldn't load member team details!", extra={"name": name})
            return

        return self.admin_session.post(
            f"orgs/{self.org_name}/teams",
            json={
                "name": name,
                "description": f"Team for {name}",
                "repo_names": [f"{self.org_name}/{name}"],
                "parent_team_id": members_team_id,
                "privacy": "closed",  # meaning that all org members can see it
            },
            headers={"Accept": "application/vnd.github.v3+json"},
        )

    def join_team(self, team_slug, username):
        """
        Add the GitHub user with the given login to the given team slug.

        https://docs.github.com/en/rest/reference/teams#add-or-update-team-membership-for-a-user
        """
        return self.admin_session.put(
            f"orgs/{self.org_name}/teams/{team_slug}/memberships/{username}",
            headers={"Accept": "application/vnd.github.v3+json"},
        )

    def leave_team(self, team_slug, username):
        """
        Remove the GitHub user with the given login from the given team slug.

        https://docs.github.com/en/rest/reference/teams#remove-team-membership-for-a-user
        """
        return self.admin_session.delete(
            f"orgs/{self.org_name}/teams/{team_slug}/memberships/{username}",
            headers={"Accept": "application/vnd.github.v3+json"},
        )

    def get_projects(self):
        # https://docs.github.com/en/rest/reference/repos#list-organization-repositories
        projects = self.admin_session.get(
            f"orgs/{self.org_name}/repos?type=public", all_pages=True
        )
        projects_with_subscribers = []
        for project in projects:
            project_name = project["name"]
            # https://docs.github.com/en/rest/reference/activity#list-watchers
            watchers = self.admin_session.get(
                f"repos/{self.org_name}/{project_name}/subscribers", all_pages=True
            )
            project["subscribers_count"] = len(watchers)
            projects_with_subscribers.append(project)
        return projects_with_subscribers

    def get_teams(self):
        # https://docs.github.com/en/rest/reference/teams#list-child-teams
        return self.admin_session.get(
            f"orgs/{self.org_name}/teams/{self.members_team_slug}/teams",
            all_pages=True,
            headers={"Accept": "application/vnd.github.hellcat-preview+json"},
        )

    def get_roadies(self):
        return self.admin_session.get(
            f"orgs/{self.org_name}/teams/{self.roadies_team_slug}/members",
            all_pages=True,
        )

    def get_members(self, team_slug=None):
        if team_slug is None:
            team_slug = self.members_team_slug
        without_2fa_ids = {user["id"] for user in self.get_without_2fa()}
        roadies_ids = {roadie["id"] for roadie in self.get_roadies()}
        all_members = self.admin_session.get(
            f"orgs/{self.org_name}/teams/{team_slug}/members", all_pages=True
        )
        members = []
        for member in all_members:
            member["is_member"] = True
            member["is_roadie"] = member["id"] in roadies_ids
            member["has_2fa"] = member["id"] not in without_2fa_ids
            members.append(member)
        return members

    def get_emails(self, user):
        """
        Gets the verified email addresses of the authenticated GitHub user.
        """
        with current_app.test_request_context("/"):
            login_user(user)
            return self.session.get("user/emails", all_pages=True)

    def get_without_2fa(self):
        """
        Gets the organization members without Two Factor Auth enabled.
        """
        return self.admin_session.get(
            f"orgs/{self.org_name}/members?filter=2fa_disabled", all_pages=True
        )

    def is_member(self, username):
        """
        Checks if the GitHub user with the given login is member of the org.
        """
        try:
            response = self.admin_session.get(
                f"orgs/{self.org_name}/members/{username}"
            )
            return response.status_code == 204
        except Exception:
            return False

    def new_roadies_issue(self, data):
        return self.new_project_issue(repo="help", org="jazzband", data=data)

    def new_project_issue(self, repo, data, org="jazzband"):
        return self.admin_session.post(f"repos/{org}/{repo}/issues", json=data)

    def enable_issues(self, project_name):
        """
        Enables the issue feature for a repository.
        https://docs.github.com/en/rest/repos/repos#update-a-repository
        """
        return self.admin_session.patch(
            f"repos/{self.org_name}/{project_name}",
            json={"has_issues": True},
            headers={"Accept": "application/vnd.github.v3+json"},
        )
