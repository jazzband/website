"""
Tests for email verification functionality.

These tests verify that the GitHubBlueprint correctly handles
email retrieval and verification for users.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask
from flask_login import current_user

from jazzband.account.blueprint import GitHubBlueprint


@pytest.fixture
def github_org_name():
    """Provide a consistent GitHub organization name for tests."""
    return "test-org-name"  # Use a test name instead of the real org name


@pytest.fixture
def github_blueprint(mocker, github_org_name):
    """Create a mock GitHubBlueprint with session for testing."""
    # Create a blueprint with necessary attributes
    blueprint = mocker.MagicMock(spec=GitHubBlueprint)
    blueprint.org_name = github_org_name

    # Create a mock session
    mock_session = mocker.MagicMock()

    # Make session a property that returns our mock
    type(blueprint).session = mocker.PropertyMock(return_value=mock_session)

    return blueprint, mock_session


@pytest.fixture
def mock_user():
    """Create a mock user for testing."""
    user = MagicMock()
    user.id = 123
    user.login = "test-user"
    user.email = "test@example.com"
    return user


def test_get_emails(github_blueprint, mock_user, mocker, app):
    """Test retrieving a user's verified email addresses."""
    blueprint, mock_session = github_blueprint

    # Setup mock response for user emails
    mock_emails = [
        {
            "email": "test@example.com",
            "verified": True,
            "primary": True,
            "visibility": "public",
        },
        {
            "email": "test2@example.com",
            "verified": True,
            "primary": False,
            "visibility": "private",
        },
        {
            "email": "unverified@example.com",
            "verified": False,
            "primary": False,
            "visibility": None,
        },
    ]
    mock_session.get.return_value = mock_emails

    # Mock flask_login.login_user and current_app
    mock_login_user = mocker.patch("jazzband.account.blueprint.login_user")
    mock_context = mocker.patch("flask.current_app.test_request_context")

    # Call the get_emails method
    with app.app_context():
        result = GitHubBlueprint.get_emails(blueprint, mock_user)

    # Verify context was created and login_user was called
    mock_context.assert_called_once()
    mock_context.return_value.__enter__.assert_called_once()
    mock_login_user.assert_called_once_with(mock_user)

    # Verify API was called correctly
    mock_session.get.assert_called_once_with("user/emails", all_pages=True)

    # Verify the result
    assert len(result) == 3
    assert result[0]["email"] == "test@example.com"
    assert result[0]["verified"] is True
    assert result[1]["email"] == "test2@example.com"
    assert result[2]["verified"] is False


@pytest.mark.parametrize(
    "emails,expected_primary,expected_verified_count",
    [
        # Case 1: Has verified primary email
        (
            [
                {"email": "primary@example.com", "verified": True, "primary": True},
                {"email": "secondary@example.com", "verified": True, "primary": False},
            ],
            "primary@example.com",
            2,
        ),
        # Case 2: No primary email but has verified emails
        (
            [
                {"email": "first@example.com", "verified": True, "primary": False},
                {"email": "second@example.com", "verified": True, "primary": False},
            ],
            "first@example.com",  # Should take the first verified email
            2,
        ),
        # Case 3: Mixture of verified and unverified emails
        (
            [
                {
                    "email": "unverified@example.com",
                    "verified": False,
                    "primary": False,
                },
                {"email": "verified@example.com", "verified": True, "primary": False},
            ],
            "verified@example.com",
            1,
        ),
        # Case 4: Only unverified emails
        (
            [
                {
                    "email": "unverified1@example.com",
                    "verified": False,
                    "primary": False,
                },
                {
                    "email": "unverified2@example.com",
                    "verified": False,
                    "primary": False,
                },
            ],
            None,  # No verified emails
            0,
        ),
        # Case 5: Empty email list
        ([], None, 0),
    ],
)
def test_get_primary_and_verified_emails(
    github_blueprint,
    mock_user,
    mocker,
    app,
    emails,
    expected_primary,
    expected_verified_count,
):
    """Test scenarios with different combinations of verified and primary emails."""
    blueprint, mock_session = github_blueprint

    # Setup mock response
    mock_session.get.return_value = emails

    # Mock necessary functions
    mocker.patch("jazzband.account.blueprint.login_user")
    mocker.patch("flask.current_app.test_request_context")

    # Call the get_emails method within app context
    with app.app_context():
        result = GitHubBlueprint.get_emails(blueprint, mock_user)

    # Count verified emails
    verified_emails = [email for email in result if email.get("verified")]

    # Get primary email, or first verified email
    primary_email = next(
        (
            email["email"]
            for email in result
            if email.get("primary") and email.get("verified")
        ),
        next((email["email"] for email in result if email.get("verified")), None),
    )

    # Verify results
    assert len(verified_emails) == expected_verified_count
    assert primary_email == expected_primary
