"""
Tests for authentication and authorization functions.

These tests cover user role checking and authentication status.
"""

from jazzband.auth import current_user_is_roadie


def test_current_user_is_roadie_unauthenticated(mocker):
    """Test current_user_is_roadie returns False for unauthenticated users."""
    mock_user = mocker.MagicMock()
    mock_user.is_authenticated = False

    mocker.patch("jazzband.auth.current_user", mock_user)

    result = current_user_is_roadie()

    assert result is False


def test_current_user_is_roadie_authenticated_non_roadie(mocker):
    """Test current_user_is_roadie returns False for authenticated non-roadie users."""
    mock_user = mocker.MagicMock()
    mock_user.is_authenticated = True
    mock_user.is_roadie = False

    mocker.patch("jazzband.auth.current_user", mock_user)

    result = current_user_is_roadie()

    assert result is False


def test_current_user_is_roadie_authenticated_roadie(mocker):
    """Test current_user_is_roadie returns True for authenticated roadie users."""
    mock_user = mocker.MagicMock()
    mock_user.is_authenticated = True
    mock_user.is_roadie = True

    mocker.patch("jazzband.auth.current_user", mock_user)

    result = current_user_is_roadie()

    assert result is True


def test_current_user_is_roadie_authenticated_roadie_none(mocker):
    """Test current_user_is_roadie handles None is_roadie value."""
    mock_user = mocker.MagicMock()
    mock_user.is_authenticated = True
    mock_user.is_roadie = None

    mocker.patch("jazzband.auth.current_user", mock_user)

    result = current_user_is_roadie()

    assert result is False


def test_current_user_is_roadie_authenticated_roadie_empty_string(mocker):
    """Test current_user_is_roadie handles empty string is_roadie value."""
    mock_user = mocker.MagicMock()
    mock_user.is_authenticated = True
    mock_user.is_roadie = ""

    mocker.patch("jazzband.auth.current_user", mock_user)

    result = current_user_is_roadie()

    assert result is False


def test_current_user_is_roadie_authenticated_roadie_truthy(mocker):
    """Test current_user_is_roadie handles truthy non-boolean is_roadie values."""
    mock_user = mocker.MagicMock()
    mock_user.is_authenticated = True
    mock_user.is_roadie = "yes"  # Truthy string

    mocker.patch("jazzband.auth.current_user", mock_user)

    result = current_user_is_roadie()

    assert result is True


def test_current_user_is_roadie_authenticated_roadie_zero(mocker):
    """Test current_user_is_roadie handles zero is_roadie value."""
    mock_user = mocker.MagicMock()
    mock_user.is_authenticated = True
    mock_user.is_roadie = 0

    mocker.patch("jazzband.auth.current_user", mock_user)

    result = current_user_is_roadie()

    assert result is False


def test_current_user_is_roadie_authenticated_roadie_one(mocker):
    """Test current_user_is_roadie handles numeric is_roadie value."""
    mock_user = mocker.MagicMock()
    mock_user.is_authenticated = True
    mock_user.is_roadie = 1

    mocker.patch("jazzband.auth.current_user", mock_user)

    result = current_user_is_roadie()

    assert result is True
