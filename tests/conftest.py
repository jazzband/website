import json
from unittest.mock import MagicMock

import pytest

from jazzband.account.blueprint import GitHubBlueprint, GitHubSession
from jazzband.db import redis
from jazzband.factory import create_app
from jazzband.projects.models import Project


# Common fixtures that can be used across test modules without explicit imports
@pytest.fixture
def github_org_name():
    """Provide a consistent GitHub organization name for tests."""
    return "test-org-name"  # Use a test name instead of the real org name


@pytest.fixture
def test_project_name():
    """Provide a consistent project name for tests."""
    return "test-project"


@pytest.fixture(scope="function")
def app():
    """Flask application fixture."""
    # Set environment variables needed for OAuth testing
    import os

    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    os.environ["FLASK_ENV"] = "testing"

    # Create real test application instead of a custom one
    app = create_app()
    app.config["TESTING"] = True
    app.config["SERVER_NAME"] = "jazzband.local"
    app.config.update(
        {
            "PREFERRED_URL_SCHEME": "http",
            "GITHUB_ORG_NAME": "test-org-name",  # Use test org name
            "GITHUB_CLIENT_ID": "test-client-id",
            "GITHUB_CLIENT_SECRET": "test-client-secret",
            "GITHUB_ADMIN_TOKEN": "test-admin-token",
            "INTERNAL_PROJECTS": [],
            "WTF_CSRF_ENABLED": False,  # Disable CSRF for testing
            "SESSION_TYPE": "null",  # Use a null session for testing
            "OAUTHLIB_INSECURE_TRANSPORT": "1",  # Allow OAuth over HTTP for testing
        }
    )
    return app


@pytest.fixture(scope="function")
def test_app_context(app):
    """Provide an application context for isolated tests.

    This is separate from the main app_context fixture to avoid conflicts.
    Only use this fixture for tests that don't need the full Jazzband app setup.
    """
    with app.app_context():
        yield


@pytest.fixture
def mock_redis_client(mocker):
    """Mock the Redis client used by the application."""
    mock_client = mocker.MagicMock()

    # Create a mock lock context manager
    mock_lock = mocker.MagicMock()
    mock_lock.__enter__.return_value = None
    mock_lock.__exit__.return_value = None

    # Make the lock method return our mock lock
    mock_client.lock.return_value = mock_lock

    # Replace the underlying Redis connection with our mock
    mocker.patch.object(redis, "_redis_client", mock_client)

    return mock_client


@pytest.fixture
def mock_response_factory(mocker):
    """Create a factory for generating mock responses with consistent structure."""

    def create_response(status_code=200, data=None):
        mock_response = mocker.MagicMock()
        mock_response.status_code = status_code
        mock_response.json.return_value = data or {"success": True}
        return mock_response

    return create_response


@pytest.fixture
def create_mock_response(mock_response_factory):
    """Helper function to create mock HTTP responses with specific status codes and data.

    This is a backwards-compatible wrapper around mock_response_factory.
    """
    return mock_response_factory


@pytest.fixture
def mock_session_factory(mocker, mock_response_factory):
    """Create a factory for generating mock sessions with consistent behavior."""

    def create_session(token="test-token", default_response=None):
        session = mocker.MagicMock()

        # Mock the token property
        token_property = mocker.PropertyMock(return_value=token)
        type(session).token = token_property

        # Set up a default response
        if default_response is None:
            default_response = mock_response_factory()

        # Configure methods to return the default response
        session.request.return_value = default_response
        session.get.return_value = default_response
        session.post.return_value = default_response
        session.patch.return_value = default_response
        session.put.return_value = default_response
        session.delete.return_value = default_response

        return session

    return create_session


@pytest.fixture
def github_blueprint(mocker, github_org_name):
    """Create a mock GitHubBlueprint with admin session for testing."""
    # Create a blueprint with necessary attributes
    blueprint = mocker.MagicMock(spec=GitHubBlueprint)
    blueprint.org_name = github_org_name
    blueprint.members_team_slug = "members"
    blueprint.roadies_team_slug = "roadies"

    # Create a mock admin session
    mock_admin_session = mocker.MagicMock()

    # Make admin_session a property that returns our mock
    type(blueprint).admin_session = mocker.PropertyMock(return_value=mock_admin_session)

    return blueprint, mock_admin_session


@pytest.fixture
def mock_user():
    """Create a mock user for testing."""
    user = MagicMock()
    user.id = 123
    user.login = "test-user"
    user.email = "test@example.com"
    return user


@pytest.fixture
def mock_github_session(mocker, mock_session_factory, mock_response_factory):
    """Create a mock GitHub session for API testing."""
    # Create a mock response
    mock_response = mock_response_factory()

    # Create a mock session with the necessary methods
    session = mock_session_factory(default_response=mock_response)

    # Add GitHubSession specific behavior
    session.spec = GitHubSession

    return session, mock_response


@pytest.fixture
def mock_github_blueprint(
    mocker, github_org_name, mock_session_factory, mock_response_factory
):
    """Create a mock GitHubBlueprint with admin session for GitHub API testing.

    Returns a tuple of (blueprint, admin_session, response) for use in tests.
    """
    # Create a mock response
    mock_response = mock_response_factory()

    # Create a mock admin session
    mock_admin_session = mock_session_factory(default_response=mock_response)

    # Create a blueprint with necessary attributes
    blueprint = mocker.MagicMock(spec=GitHubBlueprint)
    blueprint.org_name = github_org_name
    blueprint.members_team_slug = "members"
    blueprint.roadies_team_slug = "roadies"

    # Make admin_session a property that returns our mock
    type(blueprint).admin_session = mocker.PropertyMock(return_value=mock_admin_session)

    # Define the enable_issues method to actually use admin_session.patch
    def enable_issues_impl(project_name):
        return mock_admin_session.patch(
            f"repos/{github_org_name}/{project_name}",
            json={"has_issues": True},
            headers={"Accept": "application/vnd.github.v3+json"},
        )

    # Replace the mock method with our implementation
    blueprint.enable_issues.side_effect = enable_issues_impl

    return blueprint, mock_admin_session, mock_response


@pytest.fixture
def mock_project(mocker, test_project_name):
    """Create a mock Project instance."""
    # Create a mock project
    mock_project = mocker.MagicMock(spec=Project)
    mock_project.name = test_project_name
    mock_project.has_issues = False
    mock_project.transfer_issue_url = None
    mock_project.team_slug = None

    # Mock Project.query.filter.first to return our mock project
    mock_filter = mocker.MagicMock()
    mock_filter.first.return_value = mock_project

    mock_query = mocker.MagicMock()
    mock_query.filter.return_value = mock_filter

    # Set up the model class
    mocker.patch.object(Project, "query", mock_query)
    mocker.patch.object(Project, "sync", mocker.MagicMock())

    return mock_project


@pytest.fixture
def mock_hook_data(hook_type="default", test_project_name=None, github_org_name=None):
    """Create mock webhook data with different variants."""
    # Set default values if not provided
    if test_project_name is None:
        test_project_name = "test-project"
    if github_org_name is None:
        github_org_name = "test-org-name"

    base_data = {
        "repository": {
            "name": test_project_name,
            "description": "A test project",
            "html_url": f"https://github.com/{github_org_name}/{test_project_name}",
        },
        "sender": {"login": "test-user"},
    }

    if hook_type == "transfer":
        # Webhook for a project transfer to Jazzband
        base_data["action"] = "transferred"
        base_data["repository"]["has_issues"] = False

    return base_data


@pytest.fixture
def mock_roadies(mocker):
    """Create mock roadies for testing.

    This fixture creates mock roadies for testing team management and other functions
    that need to interact with roadies (Jazzband administrators).
    """
    # Create mock roadie user
    mock_roadie = mocker.MagicMock()
    mock_roadie.login = "test-roadie"

    # Create mock filter_by that returns our mock roadie
    mock_filter_by = mocker.MagicMock()
    mock_filter_by.return_value = [mock_roadie]

    # Create mock User.query with filter_by
    mock_user_query = mocker.MagicMock()
    mock_user_query.filter_by = mock_filter_by

    return mock_user_query, mock_roadie


@pytest.fixture
def mock_github_api(
    mocker, github_org_name, mock_session_factory, mock_response_factory
):
    """Create a mock GitHub API for testing.

    This fixture creates a mock GitHub API that can be used for testing
    functions that interact with the GitHub API through the GitHubBlueprint.
    """
    # Create a mock GitHub API
    mock_github = mocker.MagicMock()
    mock_github.org_name = github_org_name

    # Create a mock session
    mock_session = mock_session_factory()

    # Configure enable_issues method on the mock GitHub
    def enable_issues_impl(project_name):
        # Create a specific response for this method
        return mock_response_factory(
            status_code=200, data={"name": project_name, "has_issues": True}
        )

    mock_github.enable_issues.side_effect = enable_issues_impl

    return mock_github, mock_session


@pytest.fixture
def mock_redis_hook(mocker, mock_redis_client, mock_hook_data):
    """Mock Redis connection with prepared hook data."""
    # Mock the get operation to return our test data
    mock_redis_client.get.return_value = json.dumps(mock_hook_data)
    return mock_redis_client


# Simplified fixtures for testing specific modules
@pytest.fixture
def talisman(app):
    """Create a JazzbandTalisman instance initialized with the test app."""
    from jazzband.headers import JazzbandTalisman

    return JazzbandTalisman(app)


@pytest.fixture
def csp_test_setup():
    """Provide common CSP test setup: headers and options."""
    return {"headers": {}, "options": {"content_security_policy": "default-src self"}}


@pytest.fixture
def mock_page():
    """Create a mock page object for renderer testing."""

    class MockPage:
        def __init__(self):
            self.md = None
            self.pages = None

    return MockPage()


@pytest.fixture
def mock_flatpages():
    """Create a factory for mock flatpages objects with configurable extensions."""

    def create_flatpages(extensions=None):
        class MockFlatpages:
            def __init__(self):
                self._extensions = extensions or ["codehilite", "toc"]

            def config(self, key):
                if key == "markdown_extensions":
                    return self._extensions
                return None

        return MockFlatpages()

    return create_flatpages


@pytest.fixture
def mock_target():
    """Create a mock target object for database sync testing."""

    class MockTarget:
        def __init__(self):
            self.synced_at = None

    return MockTarget()


@pytest.fixture
def mock_response():
    """Create a simple mock response for exception testing."""

    class MockResponse:
        def __init__(
            self, json_data=None, json_error=False, content=None, has_content=True
        ):
            self._json_data = json_data
            self._json_error = json_error
            self._content = content
            self._has_content = has_content

        def json(self):
            if self._json_error:
                raise Exception("Not JSON")
            return self._json_data

        @property
        def content(self):
            if not self._has_content:
                raise AttributeError("'MockResponse' object has no attribute 'content'")
            return self._content

    return MockResponse
