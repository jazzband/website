"""
Tests for GitHub organization member management functionality.

These tests cover the member-related methods in GitHubBlueprint, including:
- Adding users to the organization
- Removing users from the organization
- Checking if a user is a member
- Getting member lists with different filters
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from jazzband.account.blueprint import GitHubBlueprint


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


# Tests for adding and removing members from the organization


def test_join_organization(app, mocker, github_org_name):
    """Test adding a user to the organization."""
    # Create a test context
    with app.test_request_context():
        username = "test-user"

        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "state": "active",
            "role": "member",
        }

        # Create a real instance of GitHubBlueprint with mocked methods
        blueprint = GitHubBlueprint("github_bp", __name__, redirect_to="index")

        # Mock the join_team method to return our prepared response
        join_team_mock = mocker.patch.object(
            GitHubBlueprint, "join_team", return_value=mock_response
        )

        # Set the required attributes directly
        blueprint.members_team_slug = "members"
        blueprint.org_name = github_org_name

        # Call the method we're testing (the real method, not a mock)
        result = blueprint.join_organization(username)

        # Verify the join_team was called with the correct parameters
        join_team_mock.assert_called_once_with("members", username)

        # Verify the result
        assert result.status_code == 200
        assert result.json()["state"] == "active"


def test_leave_organization(app, mocker, github_org_name):
    """Test removing a user from the organization."""
    # Create a test context
    with app.test_request_context():
        username = "test-user"

        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 204  # No content on successful removal

        # Create a real instance of GitHubBlueprint
        blueprint = GitHubBlueprint("github_bp", __name__, redirect_to="index")

        # Create a mock admin_session and patch the property to return it
        admin_session_mock = MagicMock()
        admin_session_mock.delete.return_value = mock_response
        mocker.patch.object(
            GitHubBlueprint,
            "admin_session",
            new_callable=mocker.PropertyMock,
            return_value=admin_session_mock,
        )

        # Set the required attributes
        blueprint.org_name = github_org_name

        # Call the actual method (not a mock)
        result = blueprint.leave_organization(username)

        # Verify the admin_session.delete was called with the expected URL
        admin_session_mock.delete.assert_called_once_with(
            f"orgs/{github_org_name}/memberships/{username}"
        )

        # Verify the result
        assert result.status_code == 204


def test_is_member_returns_true(github_blueprint, github_org_name):
    """Test checking if a user is a member when they are."""
    blueprint, mock_admin_session = github_blueprint

    username = "test-member"

    # Setup mock response for a user who is a member
    mock_response = MagicMock()
    mock_response.status_code = 204  # GitHub returns 204 if the user is a member
    mock_admin_session.get.return_value = mock_response

    # Call the is_member method
    result = GitHubBlueprint.is_member(blueprint, username)

    # Verify API was called correctly
    mock_admin_session.get.assert_called_once_with(
        f"orgs/{github_org_name}/members/{username}"
    )

    # Verify the result
    assert result is True


def test_is_member_returns_false_for_non_member(github_blueprint, github_org_name):
    """Test checking if a user is a member when they aren't."""
    blueprint, mock_admin_session = github_blueprint

    username = "non-member"

    # Setup mock response for a user who is not a member
    mock_response = MagicMock()
    mock_response.status_code = 404  # GitHub returns 404 if the user is not a member
    mock_admin_session.get.return_value = mock_response

    # Call the is_member method
    result = GitHubBlueprint.is_member(blueprint, username)

    # Verify API was called correctly
    mock_admin_session.get.assert_called_once_with(
        f"orgs/{github_org_name}/members/{username}"
    )

    # Verify the result
    assert result is False


def test_is_member_handles_exceptions(github_blueprint, github_org_name):
    """Test that is_member handles exceptions gracefully."""
    blueprint, mock_admin_session = github_blueprint

    username = "error-user"

    # Setup the admin_session.get to raise an exception
    mock_admin_session.get.side_effect = Exception("API Error")

    # Call the is_member method
    result = GitHubBlueprint.is_member(blueprint, username)

    # Verify API was called correctly
    mock_admin_session.get.assert_called_once_with(
        f"orgs/{github_org_name}/members/{username}"
    )

    # On exception, should return False
    assert result is False


# Tests for retrieving different types of member lists


def test_get_roadies(github_blueprint, github_org_name):
    """Test retrieving the list of roadies."""
    blueprint, mock_admin_session = github_blueprint

    # Setup mock response
    mock_roadies = [{"id": 111, "login": "roadie1"}, {"id": 222, "login": "roadie2"}]
    mock_admin_session.get.return_value = mock_roadies

    # Call the get_roadies method
    result = GitHubBlueprint.get_roadies(blueprint)

    # Verify API was called correctly
    mock_admin_session.get.assert_called_once_with(
        f"orgs/{github_org_name}/teams/{blueprint.roadies_team_slug}/members",
        all_pages=True,
    )

    # Verify the result
    assert len(result) == 2
    assert result[0]["login"] == "roadie1"
    assert result[1]["login"] == "roadie2"


def test_get_without_2fa(github_blueprint, github_org_name):
    """Test retrieving the list of members without two-factor authentication."""
    blueprint, mock_admin_session = github_blueprint

    # Setup mock response
    mock_without_2fa = [
        {"id": 333, "login": "user-without-2fa-1"},
        {"id": 444, "login": "user-without-2fa-2"},
    ]
    mock_admin_session.get.return_value = mock_without_2fa

    # Call the get_without_2fa method
    result = GitHubBlueprint.get_without_2fa(blueprint)

    # Verify API was called correctly
    mock_admin_session.get.assert_called_once_with(
        f"orgs/{github_org_name}/members?filter=2fa_disabled",
        all_pages=True,
    )

    # Verify the result
    assert len(result) == 2
    assert result[0]["login"] == "user-without-2fa-1"
    assert result[1]["login"] == "user-without-2fa-2"
