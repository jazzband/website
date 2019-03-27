from flask import request
from sentry_sdk import capture_message, configure_scope
from flask_github import GitHub, GitHubError


class JazzbandGitHub(GitHub):
    def init_app(self, app):
        super(JazzbandGitHub, self).init_app(app)
        # fix inconsistency in the way app instances are stored
        self.members_team_id = app.config["GITHUB_MEMBERS_TEAM_ID"]
        self.roadies_team_id = app.config["GITHUB_ROADIES_TEAM_ID"]
        self.admin_access_token = app.config["GITHUB_ADMIN_TOKEN"]
        self.org_id = app.config["GITHUB_ORG_ID"]
        self.scope = app.config["GITHUB_SCOPE"]

    def _handle_invalid_response(self):
        error = request.args.get("error")
        if error:
            with configure_scope() as scope:
                scope.set_extra(
                    "error_description", request.args.get("error_description")
                )
                scope.set_extra("error_uri", request.args.get("error_uri"))
                capture_message(f"Error during OAUTH found: {error}")

    def join_organization(self, user_login):
        """
        Adds the GitHub user with the given login to the org.
        """
        try:
            return self.put(
                "teams/%s/memberships/%s" % (self.members_team_id, user_login),
                access_token=self.admin_access_token,
            )
        except GitHubError:
            return None

    def leave_organization(self, user_login):
        """
        Remove the GitHub user with the given login from the org.
        """
        try:
            return self.delete(
                "orgs/%s/memberships/%s" % (self.org_id, user_login),
                access_token=self.admin_access_token,
            )
        except GitHubError:
            return None

    def get_projects(self):
        projects = self.get(
            "orgs/%s/repos?type=public" % self.org_id,
            all_pages=True,
            access_token=self.admin_access_token,
        )
        projects_with_subscribers = []
        for project in projects:
            watchers = self.get(
                "repos/jazzband/%s/subscribers" % project["name"],
                all_pages=True,
                access_token=self.admin_access_token,
            )
            project["subscribers_count"] = len(watchers)
            projects_with_subscribers.append(project)
        return projects_with_subscribers

    def get_roadies(self):
        return self.get(
            "teams/%d/members" % self.roadies_team_id,
            all_pages=True,
            access_token=self.admin_access_token,
        )

    def get_members(self):
        without_2fa_ids = set(user["id"] for user in self.get_without_2fa())
        roadies_ids = set(roadie["id"] for roadie in github.get_roadies())
        all_members = self.get(
            "teams/%d/members" % self.members_team_id,
            all_pages=True,
            access_token=self.admin_access_token,
        )
        members = []
        for member in all_members:
            member["is_member"] = True
            member["is_roadie"] = member["id"] in roadies_ids
            member["has_2fa"] = member["id"] not in without_2fa_ids
            members.append(member)
        return members

    def get_user(self, access_token=None):
        return self.get("user", access_token=access_token)

    def publicize_membership(self, user_login):
        """
        Publicizes the membership of the GitHub user with the given login.
        """
        self.put(
            "orgs/%s/public_members/%s" % (self.org_id, user_login),
            access_token=self.admin_access_token,
        )

    def get_emails(self, access_token=None):
        """
        Gets the verified email addresses of the authenticated GitHub user.
        """
        return self.get("user/emails", all_pages=True, access_token=access_token)

    def get_without_2fa(self):
        """
        Gets the organization members without Two Factor Auth enabled.
        """
        return self.get(
            "orgs/%s/members?filter=2fa_disabled" % self.org_id,
            all_pages=True,
            access_token=self.admin_access_token,
        )

    def is_member(self, user_login):
        """
        Checks if the GitHub user with the given login is member of the org.
        """
        try:
            self.get(
                "orgs/%s/members/%s" % (self.org_id, user_login),
                access_token=self.admin_access_token,
            )
            return True
        except GitHubError:
            return False

    def new_roadies_issue(self, data):
        return self.post(
            "repos/jazzband/roadies/issues", data, access_token=self.admin_access_token
        )


github = JazzbandGitHub()
