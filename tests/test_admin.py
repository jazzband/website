"""Tests for Flask-Admin configuration and customizations."""

from uuid import UUID, uuid4

from flask import request, session
from wtforms import StringField
from wtforms.fields.core import UnboundField

from jazzband.admin import (
    CUSTOM_FORMATTERS,
    JazzbandAdminIndexView,
    JazzbandModelView,
    ProjectCredentialAdmin,
    ProjectCredentialInlineForm,
    init_app,
    uuid_formatter,
)
from jazzband.projects.models import ProjectCredential


# Tests for UUID formatting


def test_uuid_formatter_returns_hex_string():
    """Test that uuid_formatter converts UUID to hex string."""
    test_uuid = uuid4()
    result = uuid_formatter(None, test_uuid, "key")
    assert result == test_uuid.hex
    assert isinstance(result, str)
    assert len(result) == 32  # UUID hex is 32 characters


def test_uuid_formatter_handles_none():
    """Test that uuid_formatter returns empty string for None."""
    result = uuid_formatter(None, None, "key")
    assert result == ""


def test_custom_formatters_includes_uuid():
    """Test that CUSTOM_FORMATTERS has UUID type formatter."""
    assert UUID in CUSTOM_FORMATTERS
    assert CUSTOM_FORMATTERS[UUID] is uuid_formatter


def test_jazzband_model_view_has_uuid_formatter():
    """Test that JazzbandModelView uses custom UUID formatter."""
    assert UUID in JazzbandModelView.column_type_formatters
    assert JazzbandModelView.column_type_formatters[UUID] is uuid_formatter


# Tests for ProjectCredentialInlineForm


def test_inline_form_has_key_in_form_columns():
    """Test that inline form includes key field."""
    assert "key" in ProjectCredentialInlineForm.form_columns


def test_inline_form_has_key_extra_field():
    """Test that inline form has key as extra StringField."""
    assert "key" in ProjectCredentialInlineForm.form_extra_fields
    key_field = ProjectCredentialInlineForm.form_extra_fields["key"]
    assert isinstance(key_field, UnboundField)
    assert key_field.field_class is StringField


def test_inline_form_key_is_readonly():
    """Test that inline form key field is configured as readonly."""
    widget_args = ProjectCredentialInlineForm.form_widget_args
    assert "key" in widget_args
    assert widget_args["key"]["readonly"] is True


def test_inline_form_on_model_change_generates_key(mocker):
    """Test that on_model_change generates key for new credentials."""
    inline_form = ProjectCredentialInlineForm(ProjectCredential)
    mock_form = mocker.MagicMock()
    mock_model = mocker.MagicMock()
    mock_model.key = None

    inline_form.on_model_change(mock_form, mock_model)

    assert mock_model.key is not None
    assert isinstance(mock_model.key, UUID)


def test_inline_form_on_model_change_preserves_existing_key(mocker):
    """Test that on_model_change does not overwrite existing key."""
    inline_form = ProjectCredentialInlineForm(ProjectCredential)
    mock_form = mocker.MagicMock()
    mock_model = mocker.MagicMock()
    existing_key = uuid4()
    mock_model.key = existing_key

    inline_form.on_model_change(mock_form, mock_model)

    assert mock_model.key == existing_key


# Tests for ProjectCredentialAdmin


def test_credential_admin_has_key_in_column_list():
    """Test that credential admin shows key in list view."""
    assert "key" in ProjectCredentialAdmin.column_list


def test_credential_admin_has_key_in_form_columns():
    """Test that credential admin includes key in edit form."""
    assert "key" in ProjectCredentialAdmin.form_columns


def test_credential_admin_has_key_extra_field():
    """Test that credential admin has key as extra StringField."""
    assert "key" in ProjectCredentialAdmin.form_extra_fields
    key_field = ProjectCredentialAdmin.form_extra_fields["key"]
    assert isinstance(key_field, UnboundField)
    assert key_field.field_class is StringField


def test_credential_admin_key_is_readonly():
    """Test that credential admin key field is configured as readonly."""
    widget_args = ProjectCredentialAdmin.form_widget_args
    assert "key" in widget_args
    assert widget_args["key"]["readonly"] is True


def test_credential_admin_can_view_details():
    """Test that credential admin has detail view enabled."""
    assert ProjectCredentialAdmin.can_view_details is True


def test_credential_admin_has_key_in_details():
    """Test that credential admin shows key in detail view."""
    assert "key" in ProjectCredentialAdmin.column_details_list


def test_credential_admin_on_model_change_generates_key_on_create(mocker):
    """Test that on_model_change generates key when creating new credential."""
    admin = ProjectCredentialAdmin.__new__(ProjectCredentialAdmin)
    mock_form = mocker.MagicMock()
    mock_model = mocker.MagicMock()
    mock_model.key = None

    admin.on_model_change(mock_form, mock_model, is_created=True)

    assert mock_model.key is not None
    assert isinstance(mock_model.key, UUID)


def test_credential_admin_on_model_change_preserves_key_on_create(mocker):
    """Test that on_model_change does not overwrite existing key on create."""
    admin = ProjectCredentialAdmin.__new__(ProjectCredentialAdmin)
    mock_form = mocker.MagicMock()
    mock_model = mocker.MagicMock()
    existing_key = uuid4()
    mock_model.key = existing_key

    admin.on_model_change(mock_form, mock_model, is_created=True)

    assert mock_model.key == existing_key


def test_credential_admin_on_model_change_no_key_generation_on_update(mocker):
    """Test that on_model_change does not generate key when updating."""
    admin = ProjectCredentialAdmin.__new__(ProjectCredentialAdmin)
    mock_form = mocker.MagicMock()
    mock_model = mocker.MagicMock()
    mock_model.key = None

    admin.on_model_change(mock_form, mock_model, is_created=False)

    # Key should still be None since we're not creating
    assert mock_model.key is None


# Tests for JazzbandModelView access control


def test_jazzband_model_view_is_accessible_returns_roadie_status(mocker, app):
    """Test that is_accessible returns current_user_is_roadie result."""
    with app.app_context():
        mock_is_roadie = mocker.patch("jazzband.admin.current_user_is_roadie")
        mock_is_roadie.return_value = True
        view = JazzbandModelView.__new__(JazzbandModelView)
        assert view.is_accessible() is True
        mock_is_roadie.assert_called_once()


def test_jazzband_model_view_is_accessible_returns_false_for_non_roadie(mocker, app):
    """Test that is_accessible returns False for non-roadie users."""
    with app.app_context():
        mock_is_roadie = mocker.patch("jazzband.admin.current_user_is_roadie")
        mock_is_roadie.return_value = False
        view = JazzbandModelView.__new__(JazzbandModelView)
        assert view.is_accessible() is False


def test_jazzband_model_view_inaccessible_callback_redirects(mocker, app):
    """Test that inaccessible_callback redirects to login and stores next URL."""
    with app.test_request_context("/admin/users"):
        view = JazzbandModelView.__new__(JazzbandModelView)
        response = view.inaccessible_callback("test_view")

        assert response.status_code == 302
        assert "/account/github" in response.location
        assert session.get("next") == request.url


# Tests for JazzbandAdminIndexView


def test_admin_index_view_redirects_unauthenticated_user(mocker, app):
    """Test that admin index redirects unauthenticated users to login."""
    with app.test_request_context("/admin/"):
        mock_user = mocker.patch("jazzband.admin.current_user")
        mock_user.is_authenticated = False

        view = JazzbandAdminIndexView()
        # Call the index method directly
        response = view.index()

        assert response.status_code == 302
        assert session.get("next") == request.url


def test_admin_index_view_allows_authenticated_user(mocker, app):
    """Test that admin index allows authenticated users."""
    with app.test_request_context("/admin/"):
        mock_user = mocker.patch("jazzband.admin.current_user")
        mock_user.is_authenticated = True
        view = JazzbandAdminIndexView()
        # The parent class will be called, which may raise an error
        # in test context, but we verify the auth check passes
        mocker.patch.object(view, "render", return_value="admin index page")
        response = view.index()
        assert response == "admin index page"


# Tests for ProjectCredentialInlineForm postprocess_form


def test_inline_form_postprocess_form_returns_form_class(mocker):
    """Test that postprocess_form returns the form class unchanged."""
    inline_form = ProjectCredentialInlineForm(ProjectCredential)
    mock_form_class = mocker.MagicMock()

    result = inline_form.postprocess_form(mock_form_class)

    assert result is mock_form_class


# Tests for init_app


def test_init_app_creates_admin_instance(mocker, app):
    """Test that init_app creates Flask-Admin and registers all model views."""
    with app.app_context():
        # Mock the Admin class to track calls
        mock_admin = mocker.MagicMock()
        mock_admin_class = mocker.patch("jazzband.admin.Admin", return_value=mock_admin)

        init_app(app)

        # Verify Admin was instantiated
        mock_admin_class.assert_called_once()
        call_kwargs = mock_admin_class.call_args[1]
        assert call_kwargs["name"] == "jazzband"
        assert isinstance(call_kwargs["index_view"], JazzbandAdminIndexView)

        # Verify all model views were added (7 models)
        assert mock_admin.add_view.call_count == 7
