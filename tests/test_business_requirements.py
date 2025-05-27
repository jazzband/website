"""
Value-based tests that focus on business requirements of the Jazzband website.

These tests verify that the core business functionality works correctly,
focusing on outcomes rather than implementation details.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from jazzband.projects.models import Project
from jazzband.projects.tasks import update_project_by_hook


@pytest.fixture
def project_transfer_hook_data(test_project_name):
    """
    Create mock webhook data that represents a project being transferred to Jazzband.

    This simulates the webhook payload received from GitHub when a project
    is transferred to the Jazzband organization.
    """
    return {
        "action": "transferred",
        "repository": {
            "name": test_project_name,
            "description": "A test project transferred to Jazzband",
            "html_url": f"https://github.com/jazzband/{test_project_name}",
            "has_issues": False,  # Issues are initially disabled
        },
        "sender": {
            "login": "test-user",
        },
    }


@pytest.fixture
def mock_redis_hook(mocker, project_transfer_hook_data):
    """
    Set up Redis to return our project transfer hook data.

    This mocks the Redis storage that would contain the webhook payload
    from GitHub after a project transfer.
    """
    from jazzband.projects.tasks import redis

    hook_id = "transfer-hook-123"

    # FlaskRedis doesn't have direct get/lock methods, it uses __getattr__ to delegate
    # to the underlying Redis connection. We need to patch the underlying Redis methods.
    # Mock the Redis client to return our hook data
    mock_redis_client = mocker.MagicMock()
    mock_redis_client.get.return_value = json.dumps(project_transfer_hook_data)

    # Create a mock lock context manager
    mock_lock = mocker.MagicMock()
    mock_lock.__enter__.return_value = None
    mock_lock.__exit__.return_value = None

    # Make the lock method return our mock lock
    mock_redis_client.lock.return_value = mock_lock

    # Replace the underlying Redis connection with our mock
    mocker.patch.object(redis, "_redis_client", mock_redis_client)

    return hook_id


# Using test_app and test_app_context fixtures from conftest.py


@pytest.fixture
def prepare_project_model(mocker, test_project_name):
    """
    Set up the Project model to correctly reflect a newly transferred project.

    This creates a project in our database that represents a project that
    has just been transferred to Jazzband but doesn't have issues enabled yet.
    """
    # Create a mock project without using spec since it requires app context
    mock_project = MagicMock()
    mock_project.name = test_project_name
    mock_project.has_issues = False
    mock_project.transfer_issue_url = None
    mock_project.team_slug = None

    # Mock Project.query.filter.first to return our mock project
    mock_filter = mocker.MagicMock()
    mock_filter.first.return_value = mock_project

    mock_query = mocker.MagicMock()
    mock_query.filter.return_value = mock_filter

    mocker.patch.object(Project, "query", mock_query)
    mocker.patch.object(Project, "sync", mocker.MagicMock())

    return mock_project


@pytest.mark.business
@pytest.mark.integration
def test_project_has_issues_enabled_after_transfer(
    test_app_context, mocker, mock_redis_hook, prepare_project_model, test_project_name
):
    """
    Test that a project has issues enabled after being transferred to Jazzband.

    Business requirement: When a project is transferred to Jazzband, the issues
    feature should be automatically enabled to facilitate community contributions.
    """
    # Mock the GitHub API to simulate a successful enable_issues call
    mock_github = mocker.MagicMock()

    # Create a successful response
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"name": test_project_name, "has_issues": True}

    # Make enable_issues return our successful response
    mock_github.enable_issues.return_value = mock_response

    # Mock User.query to return mock roadies (needed for the process)
    mock_roadie = mocker.MagicMock()
    mock_roadie.login = "test-roadie"

    mock_filter_by = mocker.MagicMock()
    mock_filter_by.return_value = [mock_roadie]

    mock_user_query = mocker.MagicMock()
    mock_user_query.filter_by = mock_filter_by

    # Run the hooks processing with our mocks
    with patch("jazzband.projects.tasks.github", mock_github):
        with patch("jazzband.projects.tasks.User.query", mock_user_query):
            with patch("flask.current_app.config", {"INTERNAL_PROJECTS": []}):
                # Process the webhook (this is our business action)
                update_project_by_hook(mock_redis_hook)

    # VERIFY THE BUSINESS OUTCOME:
    # 1. GitHub API was called to enable issues
    mock_github.enable_issues.assert_called_once_with(test_project_name)

    # 2. The project should have a transfer issue created to document the transfer
    prepare_project_model.create_transfer_issue.assert_called_once()

    # 3. A project team should be created for the project
    prepare_project_model.create_team.assert_called_once()

    # The test's focus is on verifying the business outcome: issues are enabled
    # after a project transfer, regardless of how that's technically implemented.


@pytest.mark.business
@pytest.mark.integration
@pytest.mark.error_handling
def test_project_team_setup_continues_even_if_issues_enabling_fails(
    test_app_context, mocker, mock_redis_hook, prepare_project_model, test_project_name
):
    """
    Test that a project still gets properly set up even if enabling issues fails.

    Business requirement: When a project is transferred to Jazzband, it should
    still be properly configured (team created, etc.) even if GitHub API calls
    to enable issues fail.
    """
    # Mock the GitHub API to simulate a failed enable_issues call
    mock_github = mocker.MagicMock()

    # Create a failed response
    failed_response = mocker.MagicMock()
    failed_response.status_code = 500
    failed_response.json.return_value = {"message": "Internal Server Error"}

    # Create a success response for retries
    success_response = mocker.MagicMock()
    success_response.status_code = 200
    success_response.json.return_value = {"name": test_project_name, "has_issues": True}

    # Make enable_issues fail first, then succeed
    mock_github.enable_issues.side_effect = [failed_response, success_response]

    # Mock User.query to return mock roadies (needed for the process)
    mock_roadie = mocker.MagicMock()
    mock_roadie.login = "test-roadie"

    mock_filter_by = mocker.MagicMock()
    mock_filter_by.return_value = [mock_roadie]

    mock_user_query = mocker.MagicMock()
    mock_user_query.filter_by = mock_filter_by

    # Run the hooks processing with our mocks
    with patch("jazzband.projects.tasks.github", mock_github):
        with patch("jazzband.projects.tasks.User.query", mock_user_query):
            with patch("flask.current_app.config", {"INTERNAL_PROJECTS": []}):
                with patch("jazzband.projects.tasks.time.sleep", mocker.MagicMock()):
                    # Process the webhook (this is our business action)
                    update_project_by_hook(mock_redis_hook)

    # VERIFY THE BUSINESS OUTCOME:
    # 1. GitHub API was called twice to enable issues (retry mechanism)
    assert mock_github.enable_issues.call_count == 2

    # 2. Even though the first API call failed, the project should still be set up correctly
    prepare_project_model.create_transfer_issue.assert_called_once()
    prepare_project_model.create_team.assert_called_once()

    # The test's focus is on verifying the business outcome: the project is
    # properly set up regardless of temporary API failures.
