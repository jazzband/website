"""
Tests for upload validation functionality.

These tests cover the refactored validation system that treats CDN propagation
delays as warnings rather than blocking errors.
"""

import json
from unittest.mock import MagicMock

import pytest
import requests
from requests.exceptions import HTTPError, RequestException, Timeout

from jazzband.projects.views import UploadReleaseView


@pytest.fixture
def upload_view():
    """Create an UploadReleaseView instance with mock upload and project."""
    view = UploadReleaseView()

    # Mock upload
    view.upload = MagicMock()
    view.upload.filename = "test-package-1.0.0.tar.gz"
    view.upload.version = "1.0.0"
    view.upload.md5_digest = "abc123"
    view.upload.sha256_digest = "def456"

    # Mock project
    view.project = MagicMock()
    view.project.pypi_json_url = "https://pypi.org/pypi/test-package/json"

    return view


@pytest.fixture
def valid_pypi_response():
    """Valid PyPI JSON response with matching file."""
    return {
        "releases": {
            "1.0.0": [
                {
                    "filename": "test-package-1.0.0.tar.gz",
                    "digests": {"md5": "abc123", "sha256": "def456"},
                }
            ]
        }
    }


@pytest.fixture
def pypi_response_with_hash_mismatch():
    """PyPI response with hash mismatch (should be an error)."""
    return {
        "releases": {
            "1.0.0": [
                {
                    "filename": "test-package-1.0.0.tar.gz",
                    "digests": {
                        "md5": "wrong123",  # Wrong hash
                        "sha256": "def456",
                    },
                }
            ]
        }
    }


def test_validate_upload_success(upload_view, valid_pypi_response, monkeypatch):
    """Test successful validation with matching hashes."""
    # Mock successful requests.get
    mock_response = MagicMock()
    mock_response.json.return_value = valid_pypi_response
    mock_response.raise_for_status.return_value = None

    def mock_get(*args, **kwargs):
        return mock_response

    monkeypatch.setattr(requests, "get", mock_get)

    success, errors, warnings = upload_view.validate_upload()

    assert success is True
    assert errors == []
    assert warnings == []


def test_validate_upload_timeout_warning(upload_view, monkeypatch):
    """Test that timeouts are treated as warnings, not errors."""

    def mock_get(*args, **kwargs):
        raise Timeout("Request timed out")

    monkeypatch.setattr(requests, "get", mock_get)

    success, errors, warnings = upload_view.validate_upload()

    assert success is True  # Should still succeed
    assert errors == []
    assert len(warnings) == 1
    assert "timed out" in warnings[0]
    assert "CDN propagation delays" in warnings[0]


def test_validate_upload_404_warning(upload_view, monkeypatch):
    """Test that 404 errors are treated as CDN delay warnings."""

    def mock_get(*args, **kwargs):
        response = MagicMock()
        response.status_code = 404
        raise HTTPError("404 Not Found", response=response)

    monkeypatch.setattr(requests, "get", mock_get)

    success, errors, warnings = upload_view.validate_upload()

    assert success is True  # Should still succeed
    assert errors == []
    assert len(warnings) == 1
    assert "not yet visible on PyPI API" in warnings[0]
    assert "CDN propagation delays" in warnings[0]


def test_validate_upload_other_http_error(upload_view, monkeypatch):
    """Test that non-404 HTTP errors are treated as real errors."""

    def mock_get(*args, **kwargs):
        response = MagicMock()
        response.status_code = 500
        raise HTTPError("500 Internal Server Error", response=response)

    monkeypatch.setattr(requests, "get", mock_get)

    success, errors, warnings = upload_view.validate_upload()

    assert success is False  # Should fail
    assert len(errors) == 1
    assert "HTTP error 500" in errors[0]
    assert warnings == []


def test_validate_upload_network_error_warning(upload_view, monkeypatch):
    """Test that network errors are treated as warnings."""

    def mock_get(*args, **kwargs):
        raise RequestException("Network error")

    monkeypatch.setattr(requests, "get", mock_get)

    success, errors, warnings = upload_view.validate_upload()

    assert success is True  # Should still succeed
    assert errors == []
    assert len(warnings) == 1
    assert "Network error during validation" in warnings[0]
    assert "verify manually" in warnings[0]


def test_validate_upload_json_parse_error(upload_view, monkeypatch):
    """Test that JSON parsing errors are treated as real errors."""
    mock_response = MagicMock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_response.raise_for_status.return_value = None

    def mock_get(*args, **kwargs):
        return mock_response

    monkeypatch.setattr(requests, "get", mock_get)

    success, errors, warnings = upload_view.validate_upload()

    assert success is False  # Should fail
    assert len(errors) == 1
    assert "parsing response from PyPI" in errors[0]
    assert warnings == []


def test_validate_upload_unknown_exception_warning(upload_view, monkeypatch):
    """Test that unknown exceptions are treated as warnings."""

    def mock_get(*args, **kwargs):
        raise Exception("Something unexpected happened")

    monkeypatch.setattr(requests, "get", mock_get)

    success, errors, warnings = upload_view.validate_upload()

    assert success is True  # Should still succeed
    assert errors == []
    assert len(warnings) == 1
    assert "Unknown error during validation" in warnings[0]
    assert "verify manually" in warnings[0]


def test_validate_upload_data_no_releases_warning(upload_view):
    """Test that missing releases are treated as CDN delay warnings."""
    data = {"releases": {}}  # No releases for this version

    success, errors, warnings = upload_view._validate_upload_data(data)

    assert success is True
    assert errors == []
    assert len(warnings) == 1
    assert "No released files found for version 1.0.0" in warnings[0]
    assert "CDN propagation delays" in warnings[0]


def test_validate_upload_data_file_not_found_warning(upload_view):
    """Test that missing specific file is treated as CDN delay warning."""
    data = {
        "releases": {
            "1.0.0": [
                {
                    "filename": "different-package-1.0.0.tar.gz",  # Different file
                    "digests": {"md5": "abc123", "sha256": "def456"},
                }
            ]
        }
    }

    success, errors, warnings = upload_view._validate_upload_data(data)

    assert success is True
    assert errors == []
    assert len(warnings) == 1
    assert "not yet visible in PyPI API" in warnings[0]
    assert "CDN propagation delays" in warnings[0]


def test_validate_upload_data_md5_hash_mismatch_error(upload_view):
    """Test that MD5 hash mismatches are treated as real errors."""
    data = {
        "releases": {
            "1.0.0": [
                {
                    "filename": "test-package-1.0.0.tar.gz",
                    "digests": {
                        "md5": "wrong123",  # Wrong MD5
                        "sha256": "def456",  # Correct SHA256
                    },
                }
            ]
        }
    }

    success, errors, warnings = upload_view._validate_upload_data(data)

    assert success is False  # Should fail due to hash mismatch
    assert len(errors) == 1
    assert "MD5 hash" in errors[0]
    assert "does not match" in errors[0]
    assert warnings == []


def test_validate_upload_data_sha256_hash_mismatch_error(upload_view):
    """Test that SHA256 hash mismatches are treated as real errors."""
    data = {
        "releases": {
            "1.0.0": [
                {
                    "filename": "test-package-1.0.0.tar.gz",
                    "digests": {
                        "md5": "abc123",  # Correct MD5
                        "sha256": "wrong456",  # Wrong SHA256
                    },
                }
            ]
        }
    }

    success, errors, warnings = upload_view._validate_upload_data(data)

    assert success is False  # Should fail due to hash mismatch
    assert len(errors) == 1
    assert "SHA256 hash" in errors[0]
    assert "does not match" in errors[0]
    assert warnings == []


def test_validate_upload_data_no_digests_warning(upload_view):
    """Test that missing digests are treated as warnings."""
    data = {
        "releases": {
            "1.0.0": [
                {
                    "filename": "test-package-1.0.0.tar.gz",
                    "digests": {},  # No digests available
                }
            ]
        }
    }

    success, errors, warnings = upload_view._validate_upload_data(data)

    assert success is True  # Should succeed despite missing digests
    assert errors == []
    assert len(warnings) == 1
    assert "No digests available" in warnings[0]


def test_validate_upload_data_partial_hash_match(upload_view):
    """Test validation when only one hash is available and matches."""
    # Only SHA256 available, MD5 missing - should succeed
    data = {
        "releases": {
            "1.0.0": [
                {
                    "filename": "test-package-1.0.0.tar.gz",
                    "digests": {
                        "sha256": "def456"  # Only SHA256, matches
                        # No MD5
                    },
                }
            ]
        }
    }

    success, errors, warnings = upload_view._validate_upload_data(data)

    assert success is True
    assert errors == []
    assert warnings == []


def test_validate_upload_timeout_parameter(upload_view, monkeypatch):
    """Test that custom timeout parameter is used."""
    call_args = []

    def mock_get(*args, **kwargs):
        call_args.append(kwargs)
        raise Timeout("Request timed out")

    monkeypatch.setattr(requests, "get", mock_get)

    # Test with custom timeout
    upload_view.validate_upload(timeout=15)

    assert len(call_args) == 1
    assert call_args[0]["timeout"] == 15


def test_validate_upload_multiple_files_in_release(upload_view, valid_pypi_response):
    """Test validation when multiple files exist for the same version."""
    # Add another file to the release
    valid_pypi_response["releases"]["1.0.0"].append(
        {
            "filename": "test-package-1.0.0-py3-none-any.whl",
            "digests": {"md5": "other123", "sha256": "other456"},
        }
    )

    success, errors, warnings = upload_view._validate_upload_data(valid_pypi_response)

    # Should find our specific file and validate it successfully
    assert success is True
    assert errors == []
    assert warnings == []


def test_validate_upload_integration_with_post_method(app, monkeypatch):
    """Test integration of validation with the post method."""
    # This test verifies the validation is properly integrated
    # and that warnings don't block releases while errors do

    view = UploadReleaseView()
    view.upload = MagicMock()
    view.upload.released_at = None
    view.upload.filename = "test-1.0.0.tar.gz"
    view.project = MagicMock()

    # Mock the validate_upload method to return warnings
    def mock_validate_upload():
        return True, [], ["CDN delay warning"]

    monkeypatch.setattr(view, "validate_upload", mock_validate_upload)

    # Mock form validation
    mock_form = MagicMock()
    mock_form.validate_on_submit.return_value = True

    # Mock twine run
    mock_twine_run = MagicMock()
    mock_twine_run.return_code = 0

    # Mock flash and other dependencies
    flash_calls = []

    def mock_flash(message, category=None):
        flash_calls.append((message, category))

    monkeypatch.setattr("jazzband.projects.views.flash", mock_flash)
    monkeypatch.setattr(
        "jazzband.projects.views.ReleaseForm", lambda **kwargs: mock_form
    )
    monkeypatch.setattr(
        "jazzband.projects.views.delegator.run", lambda cmd: mock_twine_run
    )
    monkeypatch.setattr(
        "jazzband.projects.views.tempfile.TemporaryDirectory",
        lambda: MagicMock().__enter__(),
    )
    monkeypatch.setattr("jazzband.projects.views.shutil.copy", lambda src, dst: None)
    monkeypatch.setattr("jazzband.projects.views.datetime", MagicMock())

    with app.test_request_context():
        result = view.post("test-project", 123)

    # Should have flashed the warning
    warning_flashes = [(msg, cat) for msg, cat in flash_calls if cat == "warning"]
    assert len(warning_flashes) == 1
    assert "CDN delay warning" in warning_flashes[0][0]

    # Should have flashed success message
    success_flashes = [(msg, cat) for msg, cat in flash_calls if cat == "success"]
    assert len(success_flashes) == 1

    # Upload should have been marked as released
    assert view.upload.released_at is not None
    view.upload.save.assert_called_once()


def test_validate_upload_blocks_on_hash_mismatch_error(app, monkeypatch):
    """Test that hash mismatch errors properly block the release."""
    view = UploadReleaseView()
    view.upload = MagicMock()
    view.upload.released_at = None
    view.upload.filename = "test-1.0.0.tar.gz"
    view.project = MagicMock()

    # Mock the validate_upload method to return errors
    def mock_validate_upload():
        return False, ["Hash mismatch error"], []

    monkeypatch.setattr(view, "validate_upload", mock_validate_upload)

    # Mock form validation
    mock_form = MagicMock()
    mock_form.validate_on_submit.return_value = True

    # Mock twine run success
    mock_twine_run = MagicMock()
    mock_twine_run.return_code = 0

    # Mock dependencies
    monkeypatch.setattr(
        "jazzband.projects.views.ReleaseForm", lambda **kwargs: mock_form
    )
    monkeypatch.setattr(
        "jazzband.projects.views.delegator.run", lambda cmd: mock_twine_run
    )
    monkeypatch.setattr(
        "jazzband.projects.views.tempfile.TemporaryDirectory",
        lambda: MagicMock().__enter__(),
    )
    monkeypatch.setattr("jazzband.projects.views.shutil.copy", lambda src, dst: None)

    with app.test_request_context():
        result = view.post("test-project", 123)

    # Should have added error to form
    mock_form.add_global_error.assert_called_once_with("Hash mismatch error")

    # Upload should NOT have been marked as released
    assert not hasattr(view.upload, "released_at") or view.upload.released_at is None
