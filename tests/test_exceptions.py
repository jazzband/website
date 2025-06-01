"""
Tests for exception classes and utility functions.

These tests cover custom exceptions and error handling utilities.
"""

import pytest
from werkzeug.exceptions import BadRequest

from jazzband.exceptions import RateLimit, Rollback, eject


def test_rate_limit_with_json_response(mock_response):
    """Test RateLimit exception with JSON response message."""
    response = mock_response(json_data={"message": "Rate limit exceeded"})

    exception = RateLimit(response)

    assert str(exception) == "Rate limit exceeded"
    assert exception.response == response


def test_rate_limit_with_non_json_response(mock_response):
    """Test RateLimit exception with non-JSON response."""
    response = mock_response(json_error=True, content="Rate limit error content")

    exception = RateLimit(response)

    assert str(exception) == "Rate limit error content"
    assert exception.response == response


def test_rate_limit_with_fallback_response(mock_response):
    """Test RateLimit exception falls back to response object when no content."""
    response = mock_response(json_error=True, has_content=False)

    exception = RateLimit(response)

    assert str(exception) == str(response)
    assert exception.response == response


def test_rollback_default():
    """Test Rollback exception with default propagate value."""
    exception = Rollback()

    assert exception.propagate is None


def test_rollback_with_propagate_true():
    """Test Rollback exception with propagate set to True."""
    exception = Rollback(propagate=True)

    assert exception.propagate is True


def test_rollback_with_propagate_false():
    """Test Rollback exception with propagate set to False."""
    exception = Rollback(propagate=False)

    assert exception.propagate is False


def test_eject_without_description():
    """Test eject function without description."""
    with pytest.raises(BadRequest) as exc_info:
        eject(400)

    # Should raise the exception without modifying the code
    assert exc_info.value.code == 400


def test_eject_with_description():
    """Test eject function with description added to status code."""
    with pytest.raises(BadRequest) as exc_info:
        eject(400, description="Custom error message")

    # Should modify the code to include the description
    assert exc_info.value.code == "400 Custom error message"


def test_eject_with_other_kwargs():
    """Test eject function passes through other keyword arguments."""
    with pytest.raises(BadRequest) as exc_info:
        eject(400, response="custom response")

    # Should still work with other kwargs
    assert exc_info.value.code == 400
