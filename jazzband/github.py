from flask.ext.cache import Cache
from flask.ext.github import (GitHub, GitHubError,
                              is_json_response, is_valid_response)

cache = Cache()


class JazzbandGitHub(GitHub):

    def init_app(self, app):
        super(JazzbandGitHub, self).init_app(app)
        # fix inconsistency in the way app instances are stored
        self.members_team_id = app.config['GITHUB_MEMBERS_TEAM_ID']
        self.roadies_team_id = app.config['GITHUB_ROADIES_TEAM_ID']
        self.admin_access_token = app.config['GITHUB_ADMIN_TOKEN']
        self.org_id = app.config['GITHUB_ORG_ID']
        self.scope = app.config['GITHUB_SCOPE']
        self.banned_users = app.config['GITHUB_BANNED_USERS']

    def add_to_org(self, user_login):
        """
        Adds the GitHub user with the given login to the org.
        """
        try:
            return self.put(
                'teams/%s/memberships/%s' % (self.members_team_id, user_login),
                access_token=self.admin_access_token
            )
        except GitHubError:
            return None

    @cache.memoize(timeout=60 * 15)
    def get_projects(self):
        projects = self.get(
            'orgs/%s/repos?type=public' % self.org_id,
            all_pages=True,
            access_token=self.admin_access_token,
        )
        projects_with_subscribers = []
        for project in projects:
            watchers = self.get(
                'repos/jazzband/%s/subscribers' % project['name'],
                all_pages=True,
                access_token=self.admin_access_token,
            )
            project['subscribers_count'] = len(watchers)
            projects_with_subscribers.append(project)
        return projects_with_subscribers

    @cache.memoize(timeout=60 * 15)
    def get_roadies(self):
        return self.get(
            'teams/%d/members' % self.roadies_team_id,
            all_pages=True,
            access_token=self.admin_access_token,
        )

    @cache.memoize(timeout=60 * 15)
    def get_members(self):
        return self.get(
            'teams/%d/members' % self.members_team_id,
            all_pages=True,
            access_token=self.admin_access_token,
        )

    def publicize_membership(self, user_login):
        """
        Publicizes the membership of the GitHub user with the given login.
        """
        self.put(
            'orgs/%s/public_members/%s' % (self.org_id, user_login),
            access_token=self.admin_access_token
        )

    def is_banned(self, user_login):
        """
        Returns whether or not the given user login has been banned.
        """
        return user_login in self.banned_users

    def has_verified_emails(self):
        """
        Checks if the authenticated GitHub user has any verified email
        addresses.
        """
        return any(
            [email
            for email in self.get('user/emails', all_pages=True)
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

    def raw_request(self, method, url, access_token=None, **kwargs):
        """
        Makes a HTTP request and returns the raw
        :class:`~requests.Response` object.

        """
        # Set ``Authorization`` header
        kwargs.setdefault('headers', {})
        if access_token is None:
            access_token = self.get_access_token()
        kwargs['headers'].setdefault('Authorization', 'token %s' % access_token)

        return self.session.request(method, url, allow_redirects=True, **kwargs)

    def request(self, method, resource, all_pages=False, **kwargs):
        """
        Makes a request to the given endpoint.
        Keyword arguments are passed to the :meth:`~requests.request` method.
        If the content type of the response is JSON, it will be decoded
        automatically and a dictionary will be returned.
        Otherwise the :class:`~requests.Response` object is returned.

        """
        response = self.raw_request(method, self.base_url + resource, **kwargs)

        if not is_valid_response(response):
            raise GitHubError(response)

        if is_json_response(response):
            result = response.json()
            while all_pages and response.links.get('next'):
                response = self.raw_request(method,
                                            response.links['next']['url'],
                                            **kwargs)
                if not is_valid_response(response) or \
                        not is_json_response(response):
                    raise GitHubError(response)
                result += response.json()
            return result
        else:
            return response

github = JazzbandGitHub()
