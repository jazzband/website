"""
Tests for decorator functions.

These tests cover template decorators and other function decorators
used throughout the application.
"""


def test_templated_decorator_with_dict_return(app, mocker):
    """Test templated decorator with function returning dict."""
    from jazzband.decorators import templated

    @templated("test_template.html")
    def test_view():
        return {"key": "value"}

    mock_render = mocker.MagicMock()
    mock_render.return_value = "rendered content"

    mocker.patch("jazzband.decorators.render_template", mock_render)

    with app.test_request_context():
        result = test_view()

        mock_render.assert_called_once_with("test_template.html", key="value")
        assert result == "rendered content"


def test_templated_decorator_with_none_return(app, mocker):
    """Test templated decorator with function returning None."""
    from jazzband.decorators import templated

    @templated("test_template.html")
    def test_view():
        return None

    mock_render = mocker.MagicMock()
    mock_render.return_value = "rendered content"

    mocker.patch("jazzband.decorators.render_template", mock_render)

    with app.test_request_context():
        result = test_view()

        mock_render.assert_called_once_with("test_template.html")
        assert result == "rendered content"


def test_templated_decorator_with_empty_dict_return(app, mocker):
    """Test templated decorator with function returning empty dict."""
    from jazzband.decorators import templated

    @templated("test_template.html")
    def test_view():
        return {}

    mock_render = mocker.MagicMock()
    mock_render.return_value = "rendered content"

    mocker.patch("jazzband.decorators.render_template", mock_render)

    with app.test_request_context():
        result = test_view()

        mock_render.assert_called_once_with("test_template.html")
        assert result == "rendered content"


def test_templated_decorator_with_response_return(app):
    """Test templated decorator with function returning Response object."""
    from flask import Response

    from jazzband.decorators import templated

    @templated("test_template.html")
    def test_view():
        return Response("direct response")

    with app.test_request_context():
        result = test_view()

        assert isinstance(result, Response)
        assert result.data == b"direct response"


def test_templated_decorator_with_redirect_return(app):
    """Test templated decorator with function returning redirect."""
    from flask import redirect, url_for

    from jazzband.decorators import templated

    @templated("test_template.html")
    def test_view():
        return redirect(url_for("content.index"))

    with app.test_request_context():
        result = test_view()

        assert result.status_code == 302


def test_templated_decorator_without_explicit_template(app, mocker):
    """Test templated decorator deriving template from endpoint."""
    from jazzband.decorators import templated

    @templated()
    def test_view():
        return {"key": "value"}

    mock_render = mocker.MagicMock()
    mock_render.return_value = "rendered content"

    mock_request = mocker.MagicMock()
    mock_request.endpoint = "test.view"

    mocker.patch("jazzband.decorators.render_template", mock_render)
    mocker.patch("jazzband.decorators.request", mock_request)

    with app.test_request_context("/"):
        result = test_view()

        # Should derive template name from endpoint
        mock_render.assert_called_once_with("test/view.html", key="value")
        assert result == "rendered content"


def test_templated_decorator_with_nested_endpoint(app, mocker):
    """Test templated decorator with nested endpoint names."""
    from jazzband.decorators import templated

    @templated()
    def test_view():
        return {"key": "value"}

    mock_render = mocker.MagicMock()
    mock_render.return_value = "rendered content"

    mock_request = mocker.MagicMock()
    mock_request.endpoint = "admin.users.list"

    mocker.patch("jazzband.decorators.render_template", mock_render)
    mocker.patch("jazzband.decorators.request", mock_request)

    with app.test_request_context("/"):
        result = test_view()

        # Should convert dots to slashes for template path
        mock_render.assert_called_once_with("admin/users/list.html", key="value")
        assert result == "rendered content"


def test_templated_decorator_preserves_function_metadata(app):
    """Test templated decorator preserves original function metadata."""
    from jazzband.decorators import templated

    @templated("test_template.html")
    def test_view():
        """Original docstring."""
        return {}

    assert test_view.__name__ == "test_view"
    assert test_view.__doc__ == "Original docstring."


def test_templated_decorator_with_function_arguments(app, mocker):
    """Test templated decorator works with functions that have arguments."""
    from jazzband.decorators import templated

    @templated("test_template.html")
    def test_view(arg1, arg2=None):
        return {"arg1": arg1, "arg2": arg2}

    mock_render = mocker.MagicMock()
    mock_render.return_value = "rendered content"

    mocker.patch("jazzband.decorators.render_template", mock_render)

    with app.test_request_context():
        result = test_view("value1", arg2="value2")

        mock_render.assert_called_once_with(
            "test_template.html", arg1="value1", arg2="value2"
        )
        assert result == "rendered content"


def test_templated_decorator_with_exception_in_view(app):
    """Test templated decorator handles exceptions from wrapped function."""
    import pytest

    from jazzband.decorators import templated

    @templated("test_template.html")
    def test_view():
        raise ValueError("Test error")

    with app.test_request_context():
        with pytest.raises(ValueError, match="Test error"):
            test_view()


def test_templated_decorator_with_string_return(app):
    """Test templated decorator with function returning string."""
    from jazzband.decorators import templated

    @templated("test_template.html")
    def test_view():
        return "direct string response"

    with app.test_request_context():
        result = test_view()

        # String returns should be passed through as-is
        assert result == "direct string response"


def test_templated_decorator_with_tuple_return(app, mocker):
    """Test templated decorator with function returning tuple."""
    from jazzband.decorators import templated

    @templated("test_template.html")
    def test_view():
        return {"key": "value"}, 201

    with app.test_request_context():
        result = test_view()

        # Should handle tuple returns (template context, status code)
        assert result == ({"key": "value"}, 201)


def test_templated_decorator_with_complex_template_context(app, mocker):
    """Test templated decorator with complex template context."""
    from jazzband.decorators import templated

    @templated("test_template.html")
    def test_view():
        return {
            "users": [{"name": "Alice"}, {"name": "Bob"}],
            "count": 2,
            "nested": {"data": {"value": 42}},
        }

    mock_render = mocker.MagicMock()
    mock_render.return_value = "rendered content"

    mocker.patch("jazzband.decorators.render_template", mock_render)

    with app.test_request_context():
        result = test_view()

        expected_context = {
            "users": [{"name": "Alice"}, {"name": "Bob"}],
            "count": 2,
            "nested": {"data": {"value": 42}},
        }
        mock_render.assert_called_once_with("test_template.html", **expected_context)
        assert result == "rendered content"
