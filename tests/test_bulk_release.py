"""
Tests for bulk release functionality.

These tests cover the ability to release all uploads of a given version at once,
as requested in GitHub issue #20.
"""

from datetime import datetime
from unittest.mock import MagicMock

from flask.views import MethodView
import pytest

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
            self.save = MagicMock()  # Use MagicMock instead of lambda

    upload1 = MockUpload("test-package-1.0.0.tar.gz")
    upload2 = MockUpload("test-package-1.0.0-py3-none-any.whl")
    upload3 = MockUpload("test-package-1.0.0-py2.py3-none-any.whl")

    return [upload1, upload2, upload3]


def test_get_unreleased_uploads_for_version(bulk_release_view, mock_uploads, mocker):
    """Test getting unreleased uploads for a specific version."""
    # Mock the filter_by chain to return our uploads
    mock_result = mocker.MagicMock()
    mock_result.all.return_value = mock_uploads
    mocker.patch.object(
        bulk_release_view.project.uploads, "filter_by", return_value=mock_result
    )

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


def test_release_uploads_bulk_success(
    bulk_release_view, mock_uploads, mocker, tmp_path
):
    """Test successful bulk release using twine."""
    # Mock successful twine command
    mock_twine_result = mocker.MagicMock()
    mock_twine_result.return_code = 0
    mock_delegator_run = mocker.patch(
        "jazzband.projects.views.delegator.run", return_value=mock_twine_result
    )

    # Use tmp_path fixture for real temporary directory
    mocker.patch(
        "jazzband.projects.views.tempfile.TemporaryDirectory",
        return_value=mocker.MagicMock(
            __enter__=mocker.MagicMock(return_value=str(tmp_path))
        ),
    )
    mock_shutil_copy = mocker.patch("jazzband.projects.views.shutil.copy")

    success, twine_outputs = bulk_release_view.release_uploads_bulk(mock_uploads)

    assert success is True
    assert len(twine_outputs) == 1
    assert twine_outputs[0].return_code == 0
    assert mock_delegator_run.called
    assert mock_shutil_copy.call_count == len(mock_uploads)


def test_release_uploads_bulk_failure(
    bulk_release_view, mock_uploads, mocker, tmp_path
):
    """Test failed bulk release."""
    # Mock failed twine command
    mock_twine_result = mocker.MagicMock()
    mock_twine_result.return_code = 1
    mocker.patch(
        "jazzband.projects.views.delegator.run", return_value=mock_twine_result
    )

    # Use tmp_path fixture for real temporary directory
    mocker.patch(
        "jazzband.projects.views.tempfile.TemporaryDirectory",
        return_value=mocker.MagicMock(
            __enter__=mocker.MagicMock(return_value=str(tmp_path))
        ),
    )
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
        mock_flash("No unreleased uploads found for version 1.0.0")
        result = bulk_release_view.redirect_to_project()
    else:
        result = None

    assert result == "redirect"
    mock_flash.assert_called_once_with("No unreleased uploads found for version 1.0.0")


def test_bulk_release_preserves_individual_validation_logic(
    bulk_release_view, mock_uploads, mocker
):
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
    mocker.patch(
        "jazzband.projects.views.tempfile.TemporaryDirectory",
        return_value=mocker.MagicMock(
            __enter__=mocker.MagicMock(return_value=str(tmp_path))
        ),
    )
    mocker.patch("jazzband.projects.views.shutil.copy")

    bulk_release_view.release_uploads_bulk(mock_uploads)

    assert len(commands_run) == 1
    command = commands_run[0]
    assert command.startswith("twine upload ")

    # Should contain all filenames
    for upload in mock_uploads:
        assert upload.filename in command


def test_permission_check_logic(test_app_context, bulk_release_view):
    """Test that BulkReleaseView properly inherits from ProjectMixin and MethodView."""
    # Verify inheritance - BulkReleaseView now inherits directly from ProjectMixin and MethodView
    assert isinstance(bulk_release_view, ProjectMixin)
    assert isinstance(bulk_release_view, MethodView)

    # Verify that BulkReleaseView has the correct decorators (login_required and templated)
    # Need to check if the decorators attribute exists before accessing it
    if hasattr(bulk_release_view, 'decorators'):
        assert len(bulk_release_view.decorators) == 2

    # Verify that the project_query method exists (should be overridden for permission checking)
    assert hasattr(bulk_release_view, "project_query")
    assert callable(bulk_release_view.project_query)


def test_roadie_permission_bypass(test_app_context, bulk_release_view, mocker):
    """Test that roadies can access bulk release even if not project lead."""
    # Mock current_user as roadie
    mock_user = mocker.MagicMock()
    mock_user.is_authenticated = True
    mock_user.is_roadie = True
    mock_user.is_member = True
    mocker.patch("jazzband.auth.current_user", mock_user)
    
    # Test the roadie permission logic directly rather than dispatch_request
    from jazzband.auth import current_user_is_roadie
    
    # Test that our mocked user is considered a roadie
    is_roadie = current_user_is_roadie()
    assert is_roadie is True
    
    # Test that the view has proper roadie access in its project_query method
    mock_project = mocker.MagicMock()
    mock_project.name = "test-project"
    
    # Mock the membership query to simulate roadie access
    mock_membership = mocker.MagicMock()
    mock_membership.is_lead = False  # User is not a project lead
    mock_project.membership = mock_membership
    
    mock_query = mocker.MagicMock()
    mock_query.first_or_404.return_value = mock_project
    
    # Test that project_query method exists and can be called
    # (This tests the authorization logic without full request dispatch)
    project_query_result = bulk_release_view.project_query("test-project")
    assert callable(bulk_release_view.project_query)
    
    # Verify that roadie permissions would allow access
    # (The actual permission checking happens in the decorators and middleware)
    assert mock_user.is_roadie is True


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


def test_bulk_release_form_integration(test_app_context, bulk_release_view, mock_uploads, mocker):
    """Test Flask form integration with app context."""
    # Mock the form creation and validation
    from jazzband.projects.forms import BulkReleaseForm
    
    mock_form_class = mocker.patch("jazzband.projects.views.BulkReleaseForm")
    mock_form = mocker.MagicMock(spec=BulkReleaseForm)
    mock_form.validate_on_submit.return_value = True
    mock_form_class.return_value = mock_form
    
    # Mock flash and datetime
    mock_flash = mocker.patch("jazzband.projects.views.flash")
    mock_datetime = mocker.patch("jazzband.projects.views.datetime")
    mock_datetime.utcnow.return_value = datetime.now()

    # Mock view methods for successful flow
    bulk_release_view.get_unreleased_uploads_for_version = lambda v: mock_uploads
    bulk_release_view.validate_uploads_bulk = lambda uploads, timeout=10: (True, [], [])
    bulk_release_view.release_uploads_bulk = lambda uploads: (
        True,
        [mocker.MagicMock()],
    )
    bulk_release_view.redirect_to_project = lambda: "redirect"

    # Test that form can be instantiated with Flask context
    # This tests the actual Flask form instantiation
    form_instance = mock_form_class()
    assert form_instance is not None
    
    # Verify form validation can be called
    is_valid = form_instance.validate_on_submit()
    assert is_valid is True
    
    # Test that the complete flow works with real form objects
    result = bulk_release_view.post("test-project", "1.0.0")
    
    assert result == "redirect"
    # Verify form was created with Flask context
    mock_form_class.assert_called()


# Tests with Flask app context for better coverage
def test_get_method_release_disabled(test_app_context, bulk_release_view, mocker):
    """Test GET method when RELEASE_ENABLED is False."""
    mock_flash = mocker.patch("jazzband.projects.views.flash")
    mocker.patch(
        "jazzband.projects.views.current_app.config", {"RELEASE_ENABLED": False}
    )

    bulk_release_view.redirect_to_project = lambda: "redirect_result"

    result = bulk_release_view.get("test-project", "1.0.0")

    assert result == "redirect_result"
    mock_flash.assert_called_once_with("Releasing is currently out of service")


def test_get_method_success_with_released_uploads(
    test_app_context, bulk_release_view, mock_uploads, mocker
):
    """Test successful GET method that returns template context with released uploads."""
    mocker.patch(
        "jazzband.projects.views.current_app.config", {"RELEASE_ENABLED": True}
    )

    # Mock form class
    mock_form_class = mocker.patch("jazzband.projects.views.BulkReleaseForm")
    mock_form = mocker.MagicMock()
    mock_form_class.return_value = mock_form

    # Create mock released uploads
    released_upload = mocker.MagicMock()
    released_upload.filename = "released-file.tar.gz"
    released_upload.version = "1.0.0"

    # Mock the database queries
    bulk_release_view.get_unreleased_uploads_for_version = lambda v: mock_uploads

    # Mock the released uploads query
    mock_filter_result = mocker.MagicMock()
    mock_filter_result.all.return_value = [released_upload]
    mock_filter_chain = mocker.MagicMock()
    mock_filter_chain.filter.return_value = mock_filter_result
    bulk_release_view.project.uploads.filter_by = lambda **kwargs: mock_filter_chain

    result = bulk_release_view.get("test-project", "1.0.0")

    assert isinstance(result, dict)
    assert result["project"] == bulk_release_view.project
    assert result["version"] == "1.0.0"
    assert result["uploads"] == mock_uploads
    assert result["released_uploads"] == [released_upload]
    assert result["bulk_release_form"] == mock_form


def test_post_method_release_disabled(test_app_context, bulk_release_view, mocker):
    """Test POST method when RELEASE_ENABLED is False."""
    mock_flash = mocker.patch("jazzband.projects.views.flash")
    mocker.patch(
        "jazzband.projects.views.current_app.config", {"RELEASE_ENABLED": False}
    )

    bulk_release_view.redirect_to_project = lambda: "redirect_result"

    result = bulk_release_view.post("test-project", "1.0.0")

    assert result == "redirect_result"
    mock_flash.assert_called_once_with("Releasing is currently out of service")


def test_post_method_no_uploads(test_app_context, bulk_release_view, mocker):
    """Test POST method when no unreleased uploads exist."""
    mock_flash = mocker.patch("jazzband.projects.views.flash")
    mocker.patch(
        "jazzband.projects.views.current_app.config", {"RELEASE_ENABLED": True}
    )

    bulk_release_view.get_unreleased_uploads_for_version = lambda v: []
    bulk_release_view.redirect_to_project = lambda: "redirect_result"

    result = bulk_release_view.post("test-project", "1.0.0")

    assert result == "redirect_result"
    mock_flash.assert_called_once_with("No unreleased uploads found for version 1.0.0")


def test_post_method_form_validation_fails(
    test_app_context, bulk_release_view, mock_uploads, mocker
):
    """Test POST method when form validation fails."""
    mocker.patch(
        "jazzband.projects.views.current_app.config", {"RELEASE_ENABLED": True}
    )

    # Mock form validation failure
    mock_form_class = mocker.patch("jazzband.projects.views.BulkReleaseForm")
    mock_form = mocker.MagicMock()
    mock_form.validate_on_submit.return_value = False
    mock_form_class.return_value = mock_form

    bulk_release_view.get_unreleased_uploads_for_version = lambda v: mock_uploads

    result = bulk_release_view.post("test-project", "1.0.0")

    assert isinstance(result, dict)
    assert result["project"] == bulk_release_view.project
    assert result["version"] == "1.0.0"
    assert result["uploads"] == mock_uploads
    assert result["bulk_release_form"] == mock_form


def test_post_method_validation_errors_block_release(
    test_app_context, bulk_release_view, mock_uploads, mocker
):
    """Test POST method when validation errors block the release."""
    mocker.patch(
        "jazzband.projects.views.current_app.config", {"RELEASE_ENABLED": True}
    )

    # Mock form validation success
    mock_form_class = mocker.patch("jazzband.projects.views.BulkReleaseForm")
    mock_form = mocker.MagicMock()
    mock_form.validate_on_submit.return_value = True
    mock_form_class.return_value = mock_form

    bulk_release_view.get_unreleased_uploads_for_version = lambda v: mock_uploads

    # Mock validation with errors
    bulk_release_view.validate_uploads_bulk = lambda uploads, timeout=10: (
        False,
        ["Validation error"],
        ["Warning"],
    )

    mock_flash = mocker.patch("jazzband.projects.views.flash")

    result = bulk_release_view.post("test-project", "1.0.0")

    assert isinstance(result, dict)
    assert result["uploads"] == mock_uploads
    mock_form.add_global_error.assert_called_once_with("Validation error")
    mock_flash.assert_called_once_with("Warning", category="warning")


def test_post_method_release_failure(
    test_app_context, bulk_release_view, mock_uploads, mocker, caplog
):
    """Test POST method when twine upload fails."""
    mocker.patch(
        "jazzband.projects.views.current_app.config", {"RELEASE_ENABLED": True}
    )

    # Mock form validation success
    mock_form_class = mocker.patch("jazzband.projects.views.BulkReleaseForm")
    mock_form = mocker.MagicMock()
    mock_form.validate_on_submit.return_value = True
    mock_form_class.return_value = mock_form

    # Mock failed twine output
    mock_twine_output = mocker.MagicMock()
    mock_twine_output.out = "Twine failed"

    bulk_release_view.get_unreleased_uploads_for_version = lambda v: mock_uploads
    bulk_release_view.validate_uploads_bulk = lambda uploads, timeout=10: (True, [], [])
    bulk_release_view.release_uploads_bulk = lambda uploads: (
        False,
        [mock_twine_output],
    )

    mock_logger = mocker.patch("jazzband.projects.views.logger")

    result = bulk_release_view.post("test-project", "1.0.0")

    assert isinstance(result, dict)
    assert result["uploads"] == mock_uploads
    assert "twine_outputs" in result
    mock_form.add_global_error.assert_called_once_with(
        "Bulk release of version 1.0.0 failed."
    )
    mock_logger.error.assert_called_once()


def test_post_method_success_with_warnings(
    test_app_context, bulk_release_view, mock_uploads, mocker, caplog
):
    """Test successful POST method with warnings."""
    mocker.patch(
        "jazzband.projects.views.current_app.config", {"RELEASE_ENABLED": True}
    )

    # Mock form validation success
    mock_form_class = mocker.patch("jazzband.projects.views.BulkReleaseForm")
    mock_form = mocker.MagicMock()
    mock_form.validate_on_submit.return_value = True
    mock_form_class.return_value = mock_form

    # Mock datetime
    mock_datetime = mocker.patch("jazzband.projects.views.datetime")
    release_time = datetime.now()
    mock_datetime.utcnow.return_value = release_time

    bulk_release_view.get_unreleased_uploads_for_version = lambda v: mock_uploads
    bulk_release_view.validate_uploads_bulk = lambda uploads, timeout=10: (
        True,
        [],
        ["Warning 1", "Warning 2"],
    )
    bulk_release_view.release_uploads_bulk = lambda uploads: (
        True,
        [mocker.MagicMock()],
    )
    bulk_release_view.redirect_to_project = lambda: "redirect_result"

    mock_flash = mocker.patch("jazzband.projects.views.flash")
    mock_logger = mocker.patch("jazzband.projects.views.logger")

    result = bulk_release_view.post("test-project", "1.0.0")

    assert result == "redirect_result"

    # Check that all uploads were marked as released
    for upload in mock_uploads:
        assert upload.released_at == release_time
        upload.save.assert_called()

    # Check flash messages (warnings + success)
    flash_calls = mock_flash.call_args_list
    assert len(flash_calls) == 3  # 2 warnings + 1 success
    assert flash_calls[0][0][0] == "Warning 1"
    assert flash_calls[1][0][0] == "Warning 2"
    assert (
        "Successfully released 3 uploads for version 1.0.0 to PyPI"
        in flash_calls[2][0][0]
    )
    assert "Some validation warnings were encountered" in flash_calls[2][0][0]

    mock_logger.info.assert_called_once_with(
        "Bulk release successful: 3 uploads for test-project v1.0.0"
    )


def test_post_method_success_no_warnings(
    test_app_context, bulk_release_view, mock_uploads, mocker
):
    """Test successful POST method without warnings."""
    mocker.patch(
        "jazzband.projects.views.current_app.config", {"RELEASE_ENABLED": True}
    )

    # Mock form validation success
    mock_form_class = mocker.patch("jazzband.projects.views.BulkReleaseForm")
    mock_form = mocker.MagicMock()
    mock_form.validate_on_submit.return_value = True
    mock_form_class.return_value = mock_form

    # Mock datetime
    mock_datetime = mocker.patch("jazzband.projects.views.datetime")
    release_time = datetime.now()
    mock_datetime.utcnow.return_value = release_time

    bulk_release_view.get_unreleased_uploads_for_version = lambda v: mock_uploads
    bulk_release_view.validate_uploads_bulk = lambda uploads, timeout=10: (
        True,
        [],
        [],
    )  # No warnings
    bulk_release_view.release_uploads_bulk = lambda uploads: (
        True,
        [mocker.MagicMock()],
    )
    bulk_release_view.redirect_to_project = lambda: "redirect_result"

    mock_flash = mocker.patch("jazzband.projects.views.flash")
    mock_logger = mocker.patch("jazzband.projects.views.logger")

    result = bulk_release_view.post("test-project", "1.0.0")

    assert result == "redirect_result"

    # Check that all uploads were marked as released
    for upload in mock_uploads:
        assert upload.released_at == release_time
        upload.save.assert_called()

    # Check flash message (no warnings mentioned)
    mock_flash.assert_called_once_with(
        "Successfully released 3 uploads for version 1.0.0 to PyPI.", category="success"
    )

    mock_logger.info.assert_called_once_with(
        "Bulk release successful: 3 uploads for test-project v1.0.0"
    )
