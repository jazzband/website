"""
Tests for leads team management functionality.

These tests cover:
- Creating leads teams
- Adding repositories to teams with specific permissions
- Automatic handling of lead membership changes
- Event listeners for ProjectMembership updates
"""

from unittest.mock import patch

from jazzband.account.blueprint import GitHubBlueprint
from jazzband.projects.tasks import (
    add_repo_to_members_team,
    add_user_to_leads_team,
    add_user_to_team,
    remove_user_from_leads_team,
    remove_user_from_team,
    setup_project_leads_team,
    update_all_projects_members_team,
)


# Tests for new GitHub API methods


def test_create_leads_team(
    github_blueprint, test_project_name, github_org_name, mocker
):
    """Test creating a leads sub-team under a project team."""
    blueprint, mock_admin_session = github_blueprint
    parent_team_slug = f"{test_project_name}"

    # Mock get_project_team to return parent team info
    parent_team_response = mocker.MagicMock()
    parent_team_response.status_code = 200
    parent_team_response.json.return_value = {
        "id": 12345,
        "slug": parent_team_slug,
    }
    blueprint.get_project_team.return_value = parent_team_response

    # Mock the POST request for creating the leads team
    leads_team_response = mocker.MagicMock()
    leads_team_response.status_code = 201
    leads_team_response.json.return_value = {
        "id": 67890,
        "slug": f"{test_project_name}-leads",
        "name": f"{test_project_name}-leads",
        "description": f"Lead maintainers for {test_project_name}",
    }
    mock_admin_session.post.return_value = leads_team_response

    # Call the create_leads_team method
    result = GitHubBlueprint.create_leads_team(
        blueprint, test_project_name, parent_team_slug
    )

    # Verify parent team was fetched
    blueprint.get_project_team.assert_called_once_with(parent_team_slug)

    # Verify API was called correctly
    mock_admin_session.post.assert_called_once()
    call_args = mock_admin_session.post.call_args
    assert call_args[0][0] == f"orgs/{github_org_name}/teams"
    assert call_args[1]["json"]["name"] == f"{test_project_name}-leads"
    assert call_args[1]["json"]["parent_team_id"] == 12345
    assert call_args[1]["json"]["privacy"] == "closed"

    # Verify the result
    assert result.status_code == 201
    assert result.json()["slug"] == f"{test_project_name}-leads"


def test_create_leads_team_parent_not_found(
    github_blueprint, test_project_name, mocker
):
    """Test that create_leads_team handles parent team not found."""
    blueprint, mock_admin_session = github_blueprint
    parent_team_slug = f"{test_project_name}"

    # Mock get_project_team to return 404
    parent_team_response = mocker.MagicMock()
    parent_team_response.status_code = 404
    blueprint.get_project_team.return_value = parent_team_response

    # Call the create_leads_team method
    result = GitHubBlueprint.create_leads_team(
        blueprint, test_project_name, parent_team_slug
    )

    # Verify it returns None
    assert result is None

    # Verify POST was not called
    mock_admin_session.post.assert_not_called()


def test_add_repo_to_team(github_blueprint, test_project_name, github_org_name, mocker):
    """Test adding a repository to a team with specific permissions."""
    blueprint, mock_admin_session = github_blueprint
    team_slug = "test-team"
    permission = "maintain"

    # Mock the PUT request
    mock_response = mocker.MagicMock()
    mock_response.status_code = 204  # Success returns 204 No Content
    mock_admin_session.put.return_value = mock_response

    # Call the add_repo_to_team method
    result = GitHubBlueprint.add_repo_to_team(
        blueprint, team_slug, test_project_name, permission
    )

    # Verify API was called correctly
    mock_admin_session.put.assert_called_once()
    call_args = mock_admin_session.put.call_args
    assert (
        call_args[0][0]
        == f"orgs/{github_org_name}/teams/{team_slug}/repos/{github_org_name}/{test_project_name}"
    )
    assert call_args[1]["json"]["permission"] == permission
    assert call_args[1]["headers"] == {"Accept": "application/vnd.github.v3+json"}

    # Verify the result
    assert result.status_code == 204


def test_add_repo_to_team_default_permission(
    github_blueprint, test_project_name, github_org_name, mocker
):
    """Test that add_repo_to_team uses 'push' as default permission."""
    blueprint, mock_admin_session = github_blueprint
    team_slug = "test-team"

    # Mock the PUT request
    mock_response = mocker.MagicMock()
    mock_response.status_code = 204
    mock_admin_session.put.return_value = mock_response

    # Call without specifying permission
    GitHubBlueprint.add_repo_to_team(blueprint, team_slug, test_project_name)

    # Verify default permission is 'push'
    call_args = mock_admin_session.put.call_args
    assert call_args[1]["json"]["permission"] == "push"


def test_get_team_repos(github_blueprint, github_org_name, mocker):
    """Test getting all repositories for a team."""
    blueprint, mock_admin_session = github_blueprint
    team_slug = "test-team"

    # Mock the GET request
    mock_repos = [
        {"name": "repo1", "full_name": f"{github_org_name}/repo1"},
        {"name": "repo2", "full_name": f"{github_org_name}/repo2"},
    ]
    mock_admin_session.get.return_value = mock_repos

    # Call the get_team_repos method
    result = GitHubBlueprint.get_team_repos(blueprint, team_slug)

    # Verify API was called correctly
    mock_admin_session.get.assert_called_once_with(
        f"orgs/{github_org_name}/teams/{team_slug}/repos",
        all_pages=True,
        headers={"Accept": "application/vnd.github.v3+json"},
    )

    # Verify the result
    assert len(result) == 2
    assert result[0]["name"] == "repo1"


# Tests for task functions


def test_add_user_to_team_regular_member(mocker, test_app_context):
    """Test adding a regular (non-lead) member to a project team."""
    user_id = 123
    project_id = 456
    is_lead = False

    # Create mock user and project
    mock_user = mocker.MagicMock()
    mock_user.id = user_id
    mock_user.login = "test-user"

    mock_project = mocker.MagicMock()
    mock_project.id = project_id
    mock_project.team_slug = "test-project"
    mock_project.leads_team_slug = "test-project-leads"

    # Mock User.query.get and Project.query.get
    with patch("jazzband.projects.tasks.User") as mock_user_class:
        with patch("jazzband.projects.tasks.Project") as mock_project_class:
            with patch("jazzband.projects.tasks.github") as mock_github:
                mock_user_class.query.get.return_value = mock_user
                mock_project_class.query.get.return_value = mock_project

                # Mock successful response
                mock_response = mocker.MagicMock()
                mock_response.status_code = 200
                mock_github.join_team.return_value = mock_response

                # Call the task
                add_user_to_team(user_id, project_id, is_lead)

                # Verify join_team was called once (only for main team)
                mock_github.join_team.assert_called_once_with(
                    "test-project", "test-user"
                )


def test_add_user_to_team_lead_member(mocker, test_app_context):
    """Test adding a lead member to both project team and leads team."""
    user_id = 123
    project_id = 456
    is_lead = True

    # Create mock user and project
    mock_user = mocker.MagicMock()
    mock_user.id = user_id
    mock_user.login = "test-lead"

    mock_project = mocker.MagicMock()
    mock_project.id = project_id
    mock_project.team_slug = "test-project"
    mock_project.leads_team_slug = "test-project-leads"

    # Mock User.query.get and Project.query.get
    with patch("jazzband.projects.tasks.User") as mock_user_class:
        with patch("jazzband.projects.tasks.Project") as mock_project_class:
            with patch("jazzband.projects.tasks.github") as mock_github:
                mock_user_class.query.get.return_value = mock_user
                mock_project_class.query.get.return_value = mock_project

                # Mock successful responses
                mock_response = mocker.MagicMock()
                mock_response.status_code = 200
                mock_github.join_team.return_value = mock_response

                # Call the task
                add_user_to_team(user_id, project_id, is_lead)

                # Verify join_team was called twice (main team and leads team)
                assert mock_github.join_team.call_count == 2
                calls = mock_github.join_team.call_args_list
                assert calls[0][0] == ("test-project", "test-lead")
                assert calls[1][0] == ("test-project-leads", "test-lead")


def test_add_user_to_team_lead_no_leads_team(mocker, test_app_context):
    """Test adding a lead when project has no leads team yet."""
    user_id = 123
    project_id = 456
    is_lead = True

    # Create mock user and project without leads team
    mock_user = mocker.MagicMock()
    mock_user.login = "test-lead"

    mock_project = mocker.MagicMock()
    mock_project.team_slug = "test-project"
    mock_project.leads_team_slug = None  # No leads team

    with patch("jazzband.projects.tasks.User") as mock_user_class:
        with patch("jazzband.projects.tasks.Project") as mock_project_class:
            with patch("jazzband.projects.tasks.github") as mock_github:
                mock_user_class.query.get.return_value = mock_user
                mock_project_class.query.get.return_value = mock_project

                mock_response = mocker.MagicMock()
                mock_response.status_code = 200
                mock_github.join_team.return_value = mock_response

                # Call the task
                add_user_to_team(user_id, project_id, is_lead)

                # Verify join_team was called only once (main team only)
                mock_github.join_team.assert_called_once_with(
                    "test-project", "test-lead"
                )


def test_remove_user_from_team_lead_member(mocker, test_app_context):
    """Test removing a lead from both project team and leads team."""
    user_id = 123
    project_id = 456
    is_lead = True

    # Create mock user and project
    mock_user = mocker.MagicMock()
    mock_user.login = "test-lead"

    mock_project = mocker.MagicMock()
    mock_project.team_slug = "test-project"
    mock_project.leads_team_slug = "test-project-leads"

    with patch("jazzband.projects.tasks.User") as mock_user_class:
        with patch("jazzband.projects.tasks.Project") as mock_project_class:
            with patch("jazzband.projects.tasks.github") as mock_github:
                mock_user_class.query.get.return_value = mock_user
                mock_project_class.query.get.return_value = mock_project

                # Mock successful responses
                mock_response = mocker.MagicMock()
                mock_response.status_code = 204
                mock_github.leave_team.return_value = mock_response

                # Call the task
                remove_user_from_team(user_id, project_id, is_lead)

                # Verify leave_team was called twice (leads team first, then main team)
                assert mock_github.leave_team.call_count == 2
                calls = mock_github.leave_team.call_args_list
                assert calls[0][0] == ("test-project-leads", "test-lead")
                assert calls[1][0] == ("test-project", "test-lead")


def test_add_user_to_leads_team_success(mocker, test_app_context):
    """Test successfully adding a user to a project's leads team."""
    user_id = 123
    project_id = 456

    mock_user = mocker.MagicMock()
    mock_user.login = "test-lead"

    mock_project = mocker.MagicMock()
    mock_project.name = "test-project"
    mock_project.leads_team_slug = "test-project-leads"

    with patch("jazzband.projects.tasks.User") as mock_user_class:
        with patch("jazzband.projects.tasks.Project") as mock_project_class:
            with patch("jazzband.projects.tasks.github") as mock_github:
                mock_user_class.query.get.return_value = mock_user
                mock_project_class.query.get.return_value = mock_project

                mock_response = mocker.MagicMock()
                mock_response.status_code = 200
                mock_github.join_team.return_value = mock_response

                # Call the task
                add_user_to_leads_team(user_id, project_id)

                # Verify join_team was called
                mock_github.join_team.assert_called_once_with(
                    "test-project-leads", "test-lead"
                )


def test_add_user_to_leads_team_no_leads_team(mocker, test_app_context):
    """Test adding user to leads team when project has no leads team."""
    user_id = 123
    project_id = 456

    mock_user = mocker.MagicMock()
    mock_user.login = "test-lead"

    mock_project = mocker.MagicMock()
    mock_project.name = "test-project"
    mock_project.leads_team_slug = None

    with patch("jazzband.projects.tasks.User") as mock_user_class:
        with patch("jazzband.projects.tasks.Project") as mock_project_class:
            with patch("jazzband.projects.tasks.github") as mock_github:
                mock_user_class.query.get.return_value = mock_user
                mock_project_class.query.get.return_value = mock_project

                # Call the task
                add_user_to_leads_team(user_id, project_id)

                # Verify join_team was NOT called
                mock_github.join_team.assert_not_called()


def test_remove_user_from_leads_team_success(mocker, test_app_context):
    """Test successfully removing a user from a project's leads team."""
    user_id = 123
    project_id = 456

    mock_user = mocker.MagicMock()
    mock_user.login = "test-user"

    mock_project = mocker.MagicMock()
    mock_project.name = "test-project"
    mock_project.leads_team_slug = "test-project-leads"

    with patch("jazzband.projects.tasks.User") as mock_user_class:
        with patch("jazzband.projects.tasks.Project") as mock_project_class:
            with patch("jazzband.projects.tasks.github") as mock_github:
                mock_user_class.query.get.return_value = mock_user
                mock_project_class.query.get.return_value = mock_project

                mock_response = mocker.MagicMock()
                mock_response.status_code = 204
                mock_github.leave_team.return_value = mock_response

                # Call the task
                remove_user_from_leads_team(user_id, project_id)

                # Verify leave_team was called
                mock_github.leave_team.assert_called_once_with(
                    "test-project-leads", "test-user"
                )


def test_setup_project_leads_team_success(mocker, test_app_context):
    """Test successfully setting up a leads team for a project."""
    project_id = 456

    # Create mock project with leads
    mock_project = mocker.MagicMock()
    mock_project.id = project_id
    mock_project.name = "test-project"
    mock_project.team_slug = "test-project"
    mock_project.leads_team_slug = None

    # Create mock lead members
    mock_lead1 = mocker.MagicMock()
    mock_lead1.login = "lead1"
    mock_lead2 = mocker.MagicMock()
    mock_lead2.login = "lead2"

    mock_leads_query = mocker.MagicMock()
    mock_leads_query.all.return_value = [mock_lead1, mock_lead2]
    mock_project.lead_members = mock_leads_query

    # Mock create_leads_team response
    mock_leads_response = mocker.MagicMock()
    mock_leads_response.status_code = 201
    mock_project.create_leads_team.return_value = mock_leads_response
    mock_project.leads_team_slug = "test-project-leads"  # Set after creation

    with patch("jazzband.projects.tasks.Project") as mock_project_class:
        with patch("jazzband.projects.tasks.github") as mock_github:
            mock_project_class.query.get.return_value = mock_project

            # Mock successful responses
            mock_response = mocker.MagicMock()
            mock_response.status_code = 200
            mock_github.join_team.return_value = mock_response

            mock_repo_response = mocker.MagicMock()
            mock_repo_response.status_code = 204
            mock_github.add_repo_to_team.return_value = mock_repo_response

            # Mock get_project_team to return 404 (team doesn't exist)
            mock_team_response = mocker.MagicMock()
            mock_team_response.status_code = 404
            mock_github.get_project_team.return_value = mock_team_response

            # Call the task
            setup_project_leads_team(project_id)

            # Verify create_leads_team was called
            mock_project.create_leads_team.assert_called_once()

            # Verify both leads were added to the team
            assert mock_github.join_team.call_count == 2

            # Verify repo was added to leads team with maintain permission
            mock_github.add_repo_to_team.assert_called_once_with(
                "test-project-leads", "test-project", "maintain"
            )


def test_setup_project_leads_team_no_leads(mocker, test_app_context):
    """Test setup_project_leads_team skips when project has no leads."""
    project_id = 456

    mock_project = mocker.MagicMock()
    mock_project.id = project_id
    mock_project.name = "test-project"
    mock_project.team_slug = "test-project"

    # No lead members
    mock_leads_query = mocker.MagicMock()
    mock_leads_query.all.return_value = []
    mock_project.lead_members = mock_leads_query

    with patch("jazzband.projects.tasks.Project") as mock_project_class:
        mock_project_class.query.get.return_value = mock_project

        # Call the task
        setup_project_leads_team(project_id)

        # Verify create_leads_team was NOT called
        mock_project.create_leads_team.assert_not_called()


def test_setup_project_leads_team_finds_existing(mocker, test_app_context):
    """Test that setup finds and uses manually created leads team."""
    project_id = 456

    mock_project = mocker.MagicMock()
    mock_project.id = project_id
    mock_project.name = "test-project"
    mock_project.team_slug = "test-project"
    mock_project.leads_team_slug = None

    # Create mock lead
    mock_lead = mocker.MagicMock()
    mock_lead.login = "lead1"

    mock_leads_query = mocker.MagicMock()
    mock_leads_query.all.return_value = [mock_lead]
    mock_project.lead_members = mock_leads_query

    with patch("jazzband.projects.tasks.Project") as mock_project_class:
        with patch("jazzband.projects.tasks.github") as mock_github:
            mock_project_class.query.get.return_value = mock_project

            # Mock get_project_team to return 200 (manually created team exists)
            mock_team_response = mocker.MagicMock()
            mock_team_response.status_code = 200
            mock_github.get_project_team.return_value = mock_team_response

            mock_response = mocker.MagicMock()
            mock_response.status_code = 200
            mock_github.join_team.return_value = mock_response

            mock_repo_response = mocker.MagicMock()
            mock_repo_response.status_code = 204
            mock_github.add_repo_to_team.return_value = mock_repo_response

            # Mock save to track calls
            mock_project.save = mocker.MagicMock()

            # Call the task
            setup_project_leads_team(project_id)

            # Verify get_project_team was called to check for existing team
            mock_github.get_project_team.assert_called()

            # Verify save was called (to update leads_team_slug)
            mock_project.save.assert_called()

            # Verify create_leads_team was NOT called (existing team found)
            mock_project.create_leads_team.assert_not_called()


def test_add_repo_to_members_team_success(mocker, test_app_context):
    """Test successfully adding a repo to the members team."""
    project_name = "test-project"
    permission = "push"

    with patch("jazzband.projects.tasks.github") as mock_github:
        mock_github.members_team_slug = "members"

        mock_response = mocker.MagicMock()
        mock_response.status_code = 204
        mock_github.add_repo_to_team.return_value = mock_response

        # Call the task
        add_repo_to_members_team(project_name, permission)

        # Verify add_repo_to_team was called correctly
        mock_github.add_repo_to_team.assert_called_once_with(
            "members", project_name, permission
        )


def test_update_all_projects_members_team(mocker, test_app_context):
    """Test updating all active projects to be in members team."""
    permission = "push"

    # Create mock projects
    mock_project1 = mocker.MagicMock()
    mock_project1.id = 1
    mock_project1.name = "project1"

    mock_project2 = mocker.MagicMock()
    mock_project2.id = 2
    mock_project2.name = "project2"

    with patch("jazzband.projects.tasks.Project") as mock_project_class:
        with patch("jazzband.projects.tasks.github") as mock_github:
            # Mock query to return active projects
            mock_filter_by = mocker.MagicMock()
            mock_filter_by.all.return_value = [mock_project1, mock_project2]
            mock_project_class.query.filter_by.return_value = mock_filter_by

            mock_github.members_team_slug = "members"

            # Mock successful responses
            mock_response = mocker.MagicMock()
            mock_response.status_code = 204
            mock_github.add_repo_to_team.return_value = mock_response

            # Call the task
            update_all_projects_members_team(permission)

            # Verify both projects were processed
            assert mock_github.add_repo_to_team.call_count == 2
            calls = mock_github.add_repo_to_team.call_args_list
            assert calls[0][0] == ("members", "project1", "push")
            assert calls[1][0] == ("members", "project2", "push")
