from flask.ext.github import GitHub, GitHubError


class JazzbandGitHub(GitHub):

    def init_app(self, app):
        super(JazzbandGitHub, self).init_app(app)
        # fix inconsistency in the way app instances are stored
        self.app = app
        self.member_team_id = app.config['GITHUB_MEMBERS_TEAM_ID']
        self.roadies_team_id = app.config['GITHUB_ROADIES_TEAM_ID']
        self.admin_access_token = app.config['GITHUB_ADMIN_TOKEN']
        self.org_id = app.config['GITHUB_ORG_ID']
        self.scope = app.config['GITHUB_SCOPE']

    def add_to_org(self, user_login):
        """
        Adds the GitHub user with the given login to the org.
        """
        try:
            return self.put(
                'teams/%s/memberships/%s' % (self.member_team_id, user_login),
                access_token=self.admin_access_token
            )
        except GitHubError:
            return None

    def get_projects(self):
        return self.get(
            'orgs/%s/repos?type=public' % self.org_id,
            access_token=self.admin_access_token,
        )

    def get_roadies(self):
        return self.get(
            'teams/%d/members' % self.roadies_team_id,
            access_token=self.admin_access_token
        )

    def publicize_membership(self, user_login):
        """
        Publicizes the membership of the GitHub user with the given login.
        """
        self.put(
            'orgs/%s/public_members/%s' % (self.org_id, user_login),
            access_token=self.admin_access_token
        )

    def has_verified_emails(self):
        """
        Checks if the authenticated GitHub user has any verified email addresses.
        """
        return any(
            [email for email in self.get('user/emails')
            if email.get('verified', False)],
        )

    def is_member(self, user_login):
        """
        Checks if the GitHub user with the given login is member of the org.
        """
        try:
            self.get(
                'orgs/%s/members/%s' % (self.org_id, user_login),
                access_token=self.admin_access_token,
            )
            return True
        except GitHubError:
            return False


github = JazzbandGitHub()
