from unittest.mock import patch

import pytest

from jazzband.projects.tasks import update_project_by_hook


@pytest.fixture
def mock_github(mock_github_api):
    """Mock the github object in the account module."""
    mock_github, _ = mock_github_api

    # Patch the github object
    with patch("jazzband.projects.tasks.github", mock_github):
        yield mock_github


@pytest.mark.integration
@pytest.mark.github_api
def test_update_project_by_hook_enables_issues(
    test_app_context,
    mock_redis_hook,
    mock_project,
    mock_github,
    mock_roadies,
    test_project_name,
):
    """Test that update_project_by_hook properly calls enable_issues."""
    mock_user_query, _ = mock_roadies

    with patch("jazzband.projects.tasks.User.query", mock_user_query):
        # Call the function under test
        update_project_by_hook(mock_redis_hook)

    # Verify that enable_issues was called
    mock_github.enable_issues.assert_called_once_with(test_project_name)

    # Verify that create_transfer_issue was called
    mock_project.create_transfer_issue.assert_called_once()

    # Verify that create_team was called
    mock_project.create_team.assert_called_once()


@pytest.mark.integration
@pytest.mark.github_api
@pytest.mark.error_handling
def test_update_project_by_hook_retries_enable_issues_on_failure(
    test_app_context,
    mock_redis_hook,
    mock_project,
    mock_roadies,
    mocker,
    test_project_name,
    create_mock_response,
):
    """Test that update_project_by_hook retries enable_issues on failure."""
    mock_user_query, _ = mock_roadies

    # Create mock github with failing response first, then success
    mock_github = mocker.MagicMock()

    # Create mock responses using our helper
    failed_response = create_mock_response(
        status_code=500, data={"message": "Internal Server Error"}
    )
    success_response = create_mock_response(
        status_code=200, data={"name": test_project_name, "has_issues": True}
    )

    # Set up side_effect for enable_issues to return failed response first, then success
    mock_github.enable_issues.side_effect = [failed_response, success_response]

    with patch("jazzband.projects.tasks.User.query", mock_user_query):
        with patch("jazzband.projects.tasks.github", mock_github):
            with patch(
                "jazzband.projects.tasks.time.sleep", mocker.MagicMock()
            ):  # Mock sleep to speed up test
                # Call the function under test
                update_project_by_hook(mock_redis_hook)

    # Verify that enable_issues was called twice (once for failure, once for success)
    assert mock_github.enable_issues.call_count == 2

    # Verify that create_transfer_issue was called
    mock_project.create_transfer_issue.assert_called_once()

    # Verify that create_team was called
    mock_project.create_team.assert_called_once()


@pytest.mark.integration
@pytest.mark.github_api
@pytest.mark.error_handling
def test_update_project_by_hook_aborts_after_max_retries(
    test_app_context,
    mock_redis_hook,
    mock_project,
    mock_roadies,
    mocker,
    test_project_name,
    create_mock_response,
):
    """Test that update_project_by_hook aborts after max retries for enable_issues."""
    mock_user_query, _ = mock_roadies

    # Create mock github with always failing responses
    mock_github = mocker.MagicMock()

    # All calls fail
    failed_response = create_mock_response(
        status_code=500, data={"message": "Internal Server Error"}
    )

    # Set up enable_issues to always fail
    mock_github.enable_issues.return_value = failed_response

    with patch("jazzband.projects.tasks.User.query", mock_user_query):
        with patch("jazzband.projects.tasks.github", mock_github):
            with patch(
                "jazzband.projects.tasks.time.sleep", mocker.MagicMock()
            ):  # Mock sleep to speed up test
                # Call the function under test
                update_project_by_hook(mock_redis_hook)

    # Verify that enable_issues was called 3 times (max retries)
    assert mock_github.enable_issues.call_count == 3

    # Verify that create_transfer_issue was NOT called (since we aborted)
    mock_project.create_transfer_issue.assert_not_called()

    # The create_team method should not be called here because the function
    # returns early after all retries fail
    # (In this test we're only checking the retry logic for enable_issues)
