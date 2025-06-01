"""
Tests for custom header handling.

These tests cover the JazzbandTalisman class and CSP header modification.
"""


def test_jazzband_talisman_admin_path_disables_csp(app, talisman, csp_test_setup):
    """Test JazzbandTalisman disables CSP for admin paths."""
    with app.test_request_context("/admin/some-page"):
        result = talisman._set_content_security_policy_headers(**csp_test_setup)

        # CSP should be disabled for admin paths
        assert csp_test_setup["options"]["content_security_policy"] is None


def test_jazzband_talisman_non_admin_path_keeps_csp(app, talisman, csp_test_setup):
    """Test JazzbandTalisman keeps CSP for non-admin paths."""
    original_csp = csp_test_setup["options"]["content_security_policy"]

    with app.test_request_context("/projects/"):
        result = talisman._set_content_security_policy_headers(**csp_test_setup)

        # CSP should remain unchanged for non-admin paths
        assert csp_test_setup["options"]["content_security_policy"] == original_csp


def test_jazzband_talisman_admin_subpath_disables_csp(app, talisman, csp_test_setup):
    """Test JazzbandTalisman disables CSP for admin subpaths."""
    with app.test_request_context("/admin/users/edit/123"):
        result = talisman._set_content_security_policy_headers(**csp_test_setup)

        # CSP should be disabled for admin subpaths too
        assert csp_test_setup["options"]["content_security_policy"] is None


def test_jazzband_talisman_partial_admin_match_keeps_csp(app, talisman, csp_test_setup):
    """Test JazzbandTalisman keeps CSP for paths that contain but don't start with admin."""
    original_csp = csp_test_setup["options"]["content_security_policy"]

    with app.test_request_context("/some/admin/path"):
        result = talisman._set_content_security_policy_headers(**csp_test_setup)

        # CSP should remain unchanged for paths that don't start with /admin
        assert csp_test_setup["options"]["content_security_policy"] == original_csp


def test_jazzband_talisman_with_monkeypatch(app, talisman, csp_test_setup, monkeypatch):
    """Test JazzbandTalisman behavior with monkeypatch to control request.path."""
    # Use monkeypatch to set a specific request path without needing test_request_context
    mock_request = type("MockRequest", (), {"path": "/admin/test"})()
    monkeypatch.setattr("jazzband.headers.request", mock_request)

    result = talisman._set_content_security_policy_headers(**csp_test_setup)

    # CSP should be disabled for admin paths
    assert csp_test_setup["options"]["content_security_policy"] is None
