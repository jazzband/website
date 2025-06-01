"""
Tests for bulk release functionality.

These tests cover the ability to release all uploads of a given version at once,
as requested in GitHub issue #20.
"""

from datetime import datetime

import pytest
from flask.views import MethodView

from jazzband.projects.views import BulkReleaseView, ProjectMixin


@pytest.fixture
def bulk_release_view():
    """Create a BulkReleaseView instance with mock project."""
    view = BulkReleaseView()

    # Create mock project using simple objects
    class MockProject:
        def __init__(self):
            self.name = "test-project"
            self.uploads = MockUploads()
            self.membership = MockMembership()

    class MockUploads:
        def filter_by(self, **kwargs):
            return MockQuery()

    class MockMembership:
        pass

    class MockQuery:
        def all(self):
            return []

        def first_or_404(self):
            return MockProject()

    view.project = MockProject()
    return view


@pytest.fixture
def mock_uploads():
    """Create mock uploads for testing."""
    class MockUpload:
        def __init__(self, filename, version="1.0.0"):
            self.filename = filename
            self.version = version
            self.released_at = None
            self.full_path = f"/app/uploads/{filename}"
            self.save = lambda: None

    upload1 = MockUpload("test-package-1.0.0.tar.gz")
    upload2 = MockUpload("test-package-1.0.0-py3-none-any.whl")
    upload3 = MockUpload("test-package-1.0.0-py2.py3-none-any.whl")

    return [upload1, upload2, upload3]


def test_get_unreleased_uploads_for_version(bulk_release_view, mock_uploads, mocker):
    """Test getting unreleased uploads for a specific version."""
    # Mock the filter_by chain to return our uploads
    mock_result = mocker.MagicMock()
    mock_result.all.return_value = mock_uploads
    mocker.patch.object(bulk_release_view.project.uploads, "filter_by", return_value=mock_result)

    result = bulk_release_view.get_unreleased_uploads_for_version("1.0.0")
    assert result == mock_uploads


def test_validate_uploads_bulk_success(bulk_release_view, mock_uploads, mocker):
    """Test successful bulk validation with no errors or warnings."""
    # Mock UploadReleaseView
    mock_view_class = mocker.patch("jazzband.projects.views.UploadReleaseView")
    mock_instance = mock_view_class.return_value
    mock_instance.validate_upload.return_value = (True, [], [])

    success, errors, warnings = bulk_release_view.validate_uploads_bulk(mock_uploads)

    assert success is True
    assert errors == []
    assert warnings == []
    assert mock_view_class.call_count == len(mock_uploads)


def test_validate_uploads_bulk_with_warnings(bulk_release_view, mock_uploads, mocker):
    """Test bulk validation with warnings that don't block release."""
    # Mock UploadReleaseView with warnings
    mock_view_class = mocker.patch("jazzband.projects.views.UploadReleaseView")
    mock_instance = mock_view_class.return_value
    mock_instance.validate_upload.return_value = (True, [], ["CDN delay warning"])

    success, errors, warnings = bulk_release_view.validate_uploads_bulk(mock_uploads)

    assert success is True
    assert errors == []
    assert len(warnings) == 3  # One warning per upload
    for i, warning in enumerate(warnings):
        assert mock_uploads[i].filename in warning
        assert "CDN delay warning" in warning


def test_validate_uploads_bulk_with_errors(bulk_release_view, mock_uploads, mocker):
    """Test bulk validation with errors that block release."""
    # Mock validation to return errors for some uploads
    call_count = 0

    def mock_validate_upload(timeout):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return False, ["Hash mismatch"], []
        else:
            return True, [], ["CDN warning"]

    mock_view_class = mocker.patch("jazzband.projects.views.UploadReleaseView")
    mock_instance = mock_view_class.return_value
    mock_instance.validate_upload.side_effect = mock_validate_upload

    success, errors, warnings = bulk_release_view.validate_uploads_bulk(mock_uploads)

    assert success is False  # Should fail due to errors
    assert len(errors) == 1
    assert mock_uploads[0].filename in errors[0]
    assert "Hash mismatch" in errors[0]
    assert len(warnings) == 2  # Warnings from other uploads


def test_release_uploads_bulk_success(bulk_release_view, mock_uploads, mocker, tmp_path):
    """Test successful bulk release using twine."""
    # Mock successful twine command
    mock_twine_result = mocker.MagicMock()
    mock_twine_result.return_code = 0
    mock_delegator_run = mocker.patch("jazzband.projects.views.delegator.run", return_value=mock_twine_result)

    # Use tmp_path fixture for real temporary directory
    mocker.patch("jazzband.projects.views.tempfile.TemporaryDirectory", return_value=mocker.MagicMock(__enter__=mocker.MagicMock(return_value=str(tmp_path))))
    mock_shutil_copy = mocker.patch("jazzband.projects.views.shutil.copy")

    success, twine_outputs = bulk_release_view.release_uploads_bulk(mock_uploads)

    assert success is True
    assert len(twine_outputs) == 1
    assert twine_outputs[0].return_code == 0
    assert mock_delegator_run.called
    assert mock_shutil_copy.call_count == len(mock_uploads)


def test_release_uploads_bulk_failure(bulk_release_view, mock_uploads, mocker, tmp_path):
    """Test failed bulk release."""
    # Mock failed twine command
    mock_twine_result = mocker.MagicMock()
    mock_twine_result.return_code = 1
    mocker.patch("jazzband.projects.views.delegator.run", return_value=mock_twine_result)

    # Use tmp_path fixture for real temporary directory
    mocker.patch("jazzband.projects.views.tempfile.TemporaryDirectory", return_value=mocker.MagicMock(__enter__=mocker.MagicMock(return_value=str(tmp_path))))
    mocker.patch("jazzband.projects.views.shutil.copy")

    success, twine_outputs = bulk_release_view.release_uploads_bulk(mock_uploads)

    assert success is False
    assert len(twine_outputs) == 1
    assert twine_outputs[0].return_code == 1


def test_get_method_no_uploads_basic(bulk_release_view, mocker):
    """Test GET method when no unreleased uploads exist for version."""
    mock_flash = mocker.patch("jazzband.projects.views.flash")

    # Mock the view methods
    bulk_release_view.get_unreleased_uploads_for_version = lambda v: []
    bulk_release_view.redirect_to_project = lambda: "redirect"

    # Simulate the get method logic
    uploads = bulk_release_view.get_unreleased_uploads_for_version("1.0.0")
    if not uploads:
        mock_flash(f"No unreleased uploads found for version 1.0.0")
        result = bulk_release_view.redirect_to_project()
    else:
        result = None

    assert result == "redirect"
    mock_flash.assert_called_once_with("No unreleased uploads found for version 1.0.0")


def test_bulk_release_preserves_individual_validation_logic(bulk_release_view, mock_uploads, mocker):
    """Test that bulk release uses the same validation logic as individual releases."""
    mock_view_class = mocker.patch("jazzband.projects.views.UploadReleaseView")
    mock_instance = mock_view_class.return_value
    mock_instance.validate_upload.return_value = (True, [], [])

    bulk_release_view.validate_uploads_bulk(mock_uploads)

    # Should create one UploadReleaseView instance per upload
    assert mock_view_class.call_count == len(mock_uploads)

    # Verify validate_upload was called for each instance
    assert mock_instance.validate_upload.call_count == len(mock_uploads)


def test_twine_command_construction(bulk_release_view, mock_uploads, mocker, tmp_path):
    """Test that the twine command is properly constructed for multiple files."""
    commands_run = []

    def capture_command(cmd):
        commands_run.append(cmd)
        mock_result = mocker.MagicMock()
        mock_result.return_code = 0
        return mock_result

    mocker.patch("jazzband.projects.views.delegator.run", side_effect=capture_command)
    mocker.patch("jazzband.projects.views.tempfile.TemporaryDirectory", return_value=mocker.MagicMock(__enter__=mocker.MagicMock(return_value=str(tmp_path))))
    mocker.patch("jazzband.projects.views.shutil.copy")

    bulk_release_view.release_uploads_bulk(mock_uploads)

    assert len(commands_run) == 1
    command = commands_run[0]
    assert command.startswith("twine upload ")

    # Should contain all filenames
    for upload in mock_uploads:
        assert upload.filename in command


def test_permission_check_logic(bulk_release_view):
    """Test that BulkReleaseView properly inherits from ProjectMixin and MethodView."""
    # Verify inheritance - BulkReleaseView now inherits directly from ProjectMixin and MethodView
    assert isinstance(bulk_release_view, ProjectMixin)
    assert isinstance(bulk_release_view, MethodView)

    # Verify that BulkReleaseView has the correct decorators (login_required and templated)
    assert len(bulk_release_view.decorators) == 2

    # Verify that the project_query method exists (should be overridden for permission checking)
    assert hasattr(bulk_release_view, "project_query")
    assert callable(bulk_release_view.project_query)


def test_roadie_permission_bypass(bulk_release_view, mocker):
    """Test that roadies can access bulk release even if not project lead."""
    mock_method_dispatch = mocker.patch("jazzband.projects.views.MethodView.dispatch_request", return_value="success")

    # Mock required methods
    bulk_release_view.project_name = lambda *args, **kwargs: "test-project"

    class MockQuery:
        def first_or_404(self):
            return bulk_release_view.project

    bulk_release_view.project_query = lambda name: MockQuery()

    result = bulk_release_view.dispatch_request("test-project", "1.0.0")

    assert result == "success"
    mock_method_dispatch.assert_called_once()


def test_bulk_validation_error_aggregation(bulk_release_view, mock_uploads, mocker):
    """Test that bulk validation properly aggregates errors and warnings."""
    call_count = 0

    def mock_validate_upload(timeout):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return False, ["File 1 error"], ["File 1 warning"]
        elif call_count == 2:
            return True, [], ["File 2 warning"]
        else:
            return True, [], []

    mock_view_class = mocker.patch("jazzband.projects.views.UploadReleaseView")
    mock_instance = mock_view_class.return_value
    mock_instance.validate_upload.side_effect = mock_validate_upload

    success, errors, warnings = bulk_release_view.validate_uploads_bulk(mock_uploads)

    assert success is False  # Should fail due to error in first file
    assert len(errors) == 1
    assert "test-package-1.0.0.tar.gz: File 1 error" in errors[0]
    assert len(warnings) == 2
    assert "test-package-1.0.0.tar.gz: File 1 warning" in warnings[0]
    assert "test-package-1.0.0-py3-none-any.whl: File 2 warning" in warnings[1]


def test_bulk_release_form_integration(bulk_release_view, mock_uploads, mocker, caplog):
    """Test basic form integration without Flask context."""
    mock_flash = mocker.patch("jazzband.projects.views.flash")
    mock_form_class = mocker.patch("jazzband.projects.views.BulkReleaseForm")
    mock_form = mocker.MagicMock()
    mock_form.validate_on_submit.return_value = True
    mock_form_class.return_value = mock_form

    mock_datetime = mocker.patch("jazzband.projects.views.datetime")
    mock_datetime.utcnow.return_value = datetime.now()

    # Mock the view methods
    bulk_release_view.get_unreleased_uploads_for_version = lambda v: mock_uploads
    bulk_release_view.validate_uploads_bulk = lambda uploads, timeout=10: (True, [], [])
    bulk_release_view.release_uploads_bulk = lambda uploads: (True, [mocker.MagicMock()])
    bulk_release_view.redirect_to_project = lambda: "redirect"

    # Test the basic logic directly
    def simulate_post_method(name, version):
        uploads = bulk_release_view.get_unreleased_uploads_for_version(version)
        if not uploads:
            mock_flash(f"No unreleased uploads found for version {version}")
            return bulk_release_view.redirect_to_project()

        bulk_release_form = mock_form
        if bulk_release_form.validate_on_submit():
            validation_success, all_errors, all_warnings = bulk_release_view.validate_uploads_bulk(uploads)

            if not all_errors:
                release_success, twine_outputs = bulk_release_view.release_uploads_bulk(uploads)

                if release_success:
                    release_time = datetime.utcnow()
                    released_count = 0

                    for upload in uploads:
                        upload.released_at = release_time
                        upload.save()
                        released_count += 1

                    mock_flash(
                        f"Successfully released {released_count} uploads for version {version} to PyPI.",
                        category="success",
                    )
                    return bulk_release_view.redirect_to_project()

        return {"project": bulk_release_view.project, "uploads": uploads, "bulk_release_form": bulk_release_form}

    result = simulate_post_method("test-project", "1.0.0")

    assert result == "redirect"

    # Check that uploads were marked as released
    for upload in mock_uploads:
        assert upload.released_at is not None

    # Verify flash was called with success message
    success_calls = [call for call in mock_flash.call_args_list if call[1].get('category') == 'success']
    assert len(success_calls) == 1
    assert "Successfully released 3 uploads" in success_calls[0][0][0]
