"""
Tests for GitHub team management functionality.

These tests cover the team-related methods in GitHubBlueprint, including:
- Creating project teams
- Adding users to teams
- Removing users from teams
- Getting team information
"""

from unittest.mock import MagicMock

import pytest

from jazzband.account.blueprint import GitHubBlueprint


@pytest.fixture
def github_org_name():
    """Provide a consistent GitHub organization name for tests."""
    return "test-org-name"  # Use a test name instead of the real org name


@pytest.fixture
def test_project_name():
    """Provide a consistent project name for tests."""
    return "test-project"


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


# Tests for creating and managing GitHub teams


def test_create_project_team(github_blueprint, test_project_name, github_org_name):
    """Test that a project team can be created within the members team."""
    blueprint, mock_admin_session = github_blueprint

    # Mock members team ID for parent team
    members_team_id = 98765

    # Setup mock for get_members_team_id to return our ID
    blueprint.get_members_team_id.return_value = members_team_id

    # Setup mock response for team creation
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {
        "id": 12345,
        "node_id": "MDQ6VGVhbTEyMzQ1",
        "name": test_project_name,
        "slug": test_project_name.lower(),
        "description": f"Team for {test_project_name}",
        "parent": {"slug": "members"},
    }
    mock_admin_session.post.return_value = mock_response

    # Call the create_project_team method
    result = GitHubBlueprint.create_project_team(blueprint, test_project_name)

    # Verify API was called correctly with expected data
    mock_admin_session.post.assert_called_once()
    call_args = mock_admin_session.post.call_args[0]
    call_kwargs = mock_admin_session.post.call_args[1]

    # Check that URL is correct
    assert call_args[0] == f"orgs/{github_org_name}/teams"

    # Check that JSON payload has correct structure
    assert "json" in call_kwargs
    assert call_kwargs["json"]["name"] == test_project_name
    assert call_kwargs["json"]["privacy"] == "closed"

    # Verify the result
    assert result.status_code == 201
    assert result.json()["name"] == test_project_name


def test_get_project_team(github_blueprint, test_project_name, github_org_name):
    """Test retrieving information about a specific team."""
    blueprint, mock_admin_session = github_blueprint

    team_slug = test_project_name.lower()

    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": 12345,
        "node_id": "MDQ6VGVhbTEyMzQ1",
        "name": test_project_name,
        "slug": team_slug,
        "description": f"Team for {test_project_name} project",
    }
    mock_admin_session.get.return_value = mock_response

    # Call the get_project_team method
    result = GitHubBlueprint.get_project_team(blueprint, team_slug)

    # Verify API was called correctly
    mock_admin_session.get.assert_called_once_with(
        f"orgs/{github_org_name}/teams/{team_slug}",
    )

    # Verify the result
    assert result.status_code == 200
    assert result.json()["slug"] == team_slug


def test_get_members_team_id(mocker, github_org_name):
    """Test retrieving the members team ID."""
    # Create a fully mocked blueprint instead of using app context
    blueprint = mocker.MagicMock(spec=GitHubBlueprint)
    blueprint.org_name = github_org_name
    blueprint.members_team_slug = "members"

    # Create a mock response for the team ID
    mock_team_response = MagicMock()
    mock_team_response.json.return_value = {"id": 54321}

    # Create a mock admin session
    mock_admin_session = MagicMock()
    mock_admin_session.get.return_value = mock_team_response

    # Set the admin_session property
    type(blueprint).admin_session = mocker.PropertyMock(return_value=mock_admin_session)

    # Store the original method to be able to call it
    original_method = GitHubBlueprint.get_members_team_id

    # Call the method under test
    team_id = original_method(blueprint)

    # Verify API was called correctly
    mock_admin_session.get.assert_called_once_with(
        f"orgs/{github_org_name}/teams/members"
    )

    # Verify the result
    assert team_id == 54321


def test_get_members_team_id_with_members_team_slug(mocker, github_org_name):
    """Test retrieving the members team ID with a members team slug."""
    custom_team_slug = "custom-members"

    # Create a fully mocked blueprint instead of using app context
    blueprint = mocker.MagicMock(spec=GitHubBlueprint)
    blueprint.org_name = github_org_name
    blueprint.members_team_slug = custom_team_slug

    # Create a mock response for the team ID
    mock_team_response = MagicMock()
    mock_team_response.json.return_value = {"id": 98765}

    # Create a mock admin session
    mock_admin_session = MagicMock()
    mock_admin_session.get.return_value = mock_team_response

    # Set the admin_session property
    type(blueprint).admin_session = mocker.PropertyMock(return_value=mock_admin_session)

    # Store the original method to be able to call it
    original_method = GitHubBlueprint.get_members_team_id

    # Call the method under test
    team_id = original_method(blueprint)

    # Verify API was called correctly
    mock_admin_session.get.assert_called_once_with(
        f"orgs/{github_org_name}/teams/{custom_team_slug}"
    )

    # Verify the result
    assert team_id == 98765


# Tests for adding and removing users from teams


def test_join_team(github_blueprint, github_org_name):
    """Test adding a user to a team."""
    blueprint, mock_admin_session = github_blueprint
    team_slug = "test-team"
    username = "test-user"

    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "state": "active",
        "role": "member",
    }
    mock_admin_session.put.return_value = mock_response

    # Call the join_team method
    result = GitHubBlueprint.join_team(blueprint, team_slug, username)

    # Verify API was called correctly - check that the call was made with the correct URL
    # without being strict about parameter order which can cause test failures
    mock_admin_session.put.assert_called_once()
    call_args = mock_admin_session.put.call_args
    assert (
        call_args[0][0]
        == f"orgs/{github_org_name}/teams/{team_slug}/memberships/{username}"
    )
    assert "headers" in call_args[1]
    assert call_args[1]["headers"] == {"Accept": "application/vnd.github.v3+json"}

    # Verify the result
    assert result.status_code == 200
    assert result.json()["state"] == "active"


def test_leave_team(github_blueprint, github_org_name):
    """Test removing a user from a team."""
    blueprint, mock_admin_session = github_blueprint
    team_slug = "test-team"
    username = "test-user"

    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 204  # No content on successful removal
    mock_admin_session.delete.return_value = mock_response

    # Call the leave_team method
    result = GitHubBlueprint.leave_team(blueprint, team_slug, username)

    # Verify API was called correctly
    mock_admin_session.delete.assert_called_once_with(
        f"orgs/{github_org_name}/teams/{team_slug}/memberships/{username}",
        headers={"Accept": "application/vnd.github.v3+json"},
    )

    # Verify the result
    assert result.status_code == 204


# Tests for listing teams and members


def test_get_teams(github_blueprint, test_project_name, github_org_name):
    """Test listing all child teams of the members team."""
    blueprint, mock_admin_session = github_blueprint

    # Setup mock response
    mock_response = [
        {
            "id": 12345,
            "name": test_project_name,
            "slug": test_project_name.lower(),
            "description": f"Team for {test_project_name} project",
        },
        {
            "id": 67890,
            "name": "another-project",
            "slug": "another-project",
            "description": "Team for another-project project",
        },
    ]
    mock_admin_session.get.return_value = mock_response

    # Call the get_teams method
    result = GitHubBlueprint.get_teams(blueprint)

    # Verify API was called correctly
    mock_admin_session.get.assert_called_once_with(
        f"orgs/{github_org_name}/teams/{blueprint.members_team_slug}/teams",
        all_pages=True,
        headers={"Accept": "application/vnd.github.hellcat-preview+json"},
    )

    # Verify the result
    assert len(result) == 2
    assert result[0]["name"] == test_project_name


def test_get_members(github_blueprint, mocker, github_org_name):
    """Test listing all members of a team with additional metadata."""
    blueprint, mock_admin_session = github_blueprint

    team_slug = "members"

    # Setup mock member data
    member1 = {"id": 111, "login": "member1"}
    member2 = {"id": 222, "login": "member2"}
    roadie1 = {"id": 333, "login": "roadie1"}

    # Setup mock responses for the API calls
    mock_members = [member1, member2, roadie1]

    # Users with special roles
    mock_roadies = [roadie1]  # User 333 is a roadie
    mock_without_2fa = [member2]  # User 222 has no 2FA

    # Mock the methods that fetch additional data
    # When GitHubBlueprint.get_roadies is called, return mock_roadies
    blueprint.get_roadies = MagicMock(return_value=mock_roadies)

    # When GitHubBlueprint.get_without_2fa is called, return mock_without_2fa
    blueprint.get_without_2fa = MagicMock(return_value=mock_without_2fa)

    # Setup admin_session.get to return the members
    mock_admin_session.get.return_value = mock_members

    # Call the get_members method (the function under test)
    result = GitHubBlueprint.get_members(blueprint, team_slug)

    # Verify API was called correctly
    mock_admin_session.get.assert_called_once_with(
        f"orgs/{github_org_name}/teams/{team_slug}/members",
        all_pages=True,
    )

    # Verify the result contains all members
    assert len(result) == 3

    # Extract members by login for easier testing
    result_by_login = {member["login"]: member for member in result}

    # Test member1: Regular member with 2FA
    assert result_by_login["member1"]["is_member"] is True
    assert result_by_login["member1"]["is_roadie"] is False
    assert result_by_login["member1"]["has_2fa"] is True

    # Test member2: Regular member without 2FA
    assert result_by_login["member2"]["is_member"] is True
    assert result_by_login["member2"]["is_roadie"] is False
    assert result_by_login["member2"]["has_2fa"] is False

    # Test roadie1: Roadie with 2FA
    assert result_by_login["roadie1"]["is_member"] is True
    assert result_by_login["roadie1"]["is_roadie"] is True
    assert result_by_login["roadie1"]["has_2fa"] is True
