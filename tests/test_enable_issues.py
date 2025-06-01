import pytest


@pytest.fixture
def test_project_name():
    """Provide a consistent project name for tests."""
    return "test-project"


@pytest.mark.unit
@pytest.mark.github_api
def test_enable_issues_success(mock_github_blueprint, test_project_name):
    """Test successful enabling of issues for a repository."""
    mock_blueprint, mock_admin_session, mock_response = mock_github_blueprint
    expected_url = f"repos/{mock_blueprint.org_name}/{test_project_name}"

    # Configure the mock response
    mock_response.status_code = 200
    mock_response.json.return_value = {"name": test_project_name, "has_issues": True}

    # Call the method under test
    response = mock_blueprint.enable_issues(test_project_name)

    # Verify the response
    assert response.status_code == 200
    assert response.json()["has_issues"] is True

    # Verify the request was made correctly
    mock_admin_session.patch.assert_called_once_with(
        expected_url,
        json={"has_issues": True},
        headers={"Accept": "application/vnd.github.v3+json"},
    )


@pytest.mark.unit
@pytest.mark.github_api
@pytest.mark.error_handling
def test_enable_issues_failure(mock_github_blueprint, mocker, test_project_name):
    """Test failure when enabling issues for a repository."""
    mock_blueprint, mock_admin_session, mock_response = mock_github_blueprint
    expected_url = f"repos/{mock_blueprint.org_name}/{test_project_name}"

    # Configure the mock response for failure
    mock_response.status_code = 404
    mock_response.json.return_value = {"message": "Repository not found"}

    # Call the method under test
    response = mock_blueprint.enable_issues(test_project_name)

    # Verify the response
    assert response.status_code == 404
    assert "not found" in response.json()["message"]

    # Verify the request was made correctly
    mock_admin_session.patch.assert_called_once_with(
        expected_url,
        json={"has_issues": True},
        headers={"Accept": "application/vnd.github.v3+json"},
    )
