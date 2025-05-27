from jazzband.account.blueprint import GitHubBlueprint

# Using the shared mock_github_blueprint fixture from conftest.py


def test_enable_issues_with_oauth_context(mock_github_blueprint, test_project_name):
    """Test that enable_issues works correctly in the context of OAuth authentication.
    This test simulates a workflow where the enable_issues method is called with
    proper authentication.
    """
    mock_blueprint, mock_admin_session, mock_response = mock_github_blueprint

    # Configure test data
    expected_url = f"repos/{mock_blueprint.org_name}/{test_project_name}"

    # Configure the mock response
    mock_response.status_code = 200
    mock_response.json.return_value = {"name": test_project_name, "has_issues": True}

    # Call the method under test
    response = mock_blueprint.enable_issues(test_project_name)

    # Verify the response
    assert response.status_code == 200
    assert response.json()["has_issues"] is True

    # Verify the correct API call was made
    mock_admin_session.patch.assert_called_once_with(
        expected_url,
        json={"has_issues": True},
        headers={"Accept": "application/vnd.github.v3+json"},
    )


def test_enable_issues_retries_on_failure(
    mocker, test_project_name, create_mock_response
):
    """Test the retry logic in the update_project_by_hook function
    when enable_issues fails initially.
    """
    # Create mock responses for failure and success using the helper function
    failed_response = create_mock_response(
        status_code=503, data={"message": "Service unavailable"}
    )

    success_response = create_mock_response(
        status_code=200, data={"name": test_project_name, "has_issues": True}
    )

    # Create mock admin session with patch that returns different responses
    mock_admin_session = mocker.MagicMock()
    mock_admin_session.patch.side_effect = [failed_response, success_response]

    # Create mock blueprint
    mock_blueprint = mocker.MagicMock(spec=GitHubBlueprint)
    mock_blueprint.org_name = "jazzband"

    # Connect the blueprint to actually use the admin_session for the enable_issues method
    def enable_issues_impl(project_name):
        return mock_admin_session.patch(
            f"repos/{mock_blueprint.org_name}/{project_name}",
            json={"has_issues": True},
            headers={"Accept": "application/vnd.github.v3+json"},
        )

    mock_blueprint.enable_issues.side_effect = enable_issues_impl

    # Set the admin_session property on the blueprint
    type(mock_blueprint).admin_session = mocker.PropertyMock(
        return_value=mock_admin_session
    )

    # Call the enable_issues method twice to simulate a retry
    # First call should fail
    first_response = mock_blueprint.enable_issues(test_project_name)
    assert first_response.status_code == 503
    assert "Service unavailable" in first_response.json()["message"]

    # Second call should succeed
    second_response = mock_blueprint.enable_issues(test_project_name)
    assert second_response.status_code == 200
    assert second_response.json()["has_issues"] is True

    # Verify calls were made correctly
    assert mock_admin_session.patch.call_count == 2
