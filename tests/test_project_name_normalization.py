"""Function-based tests for project name normalization and canonical URL redirects.

Converted from class-based tests to follow `AGENTS.md` testing conventions.
"""

import pytest
from werkzeug.exceptions import NotFound

from jazzband.projects.views import ProjectMixin


def test_project_query_uses_normalized_name(app, mocker):
    """ProjectMixin.project_query should use normalized name for lookup."""
    with app.app_context():
        mock_query = mocker.MagicMock()
        mock_query.filter.return_value = mock_query

        mocker.patch("jazzband.projects.views.Project.query", mock_query)

        mixin = ProjectMixin()
        mixin.project_query("Watson")

        assert mock_query.filter.called


def test_project_name_returns_name_from_kwargs(app):
    """ProjectMixin.project_name should return name from kwargs."""
    with app.app_context():
        mixin = ProjectMixin()
        assert mixin.project_name(name="test-project") == "test-project"


def test_project_name_aborts_if_no_name(app):
    """ProjectMixin.project_name should abort with NotFound if no name provided."""
    with app.app_context():
        mixin = ProjectMixin()
        with pytest.raises(NotFound):
            mixin.project_name()


def test_lowercase_url_finds_capitalized_project(app, mocker):
    """/projects/watson should redirect to canonical /projects/Watson."""
    with app.test_client() as client:
        mock_project = mocker.MagicMock()
        mock_project.name = "Watson"
        mock_project.is_active = True

        mock_query = mocker.MagicMock()
        mock_query.filter.return_value.first_or_404.return_value = mock_project

        mocker.patch("jazzband.projects.views.Project.query", mock_query)

        response = client.get("/projects/watson", follow_redirects=False)

        assert response.status_code == 301
        assert "/projects/Watson" in response.headers["Location"]


def test_canonical_url_does_not_redirect(app, mocker):
    """Canonical URL should not redirect."""
    with app.test_client() as client:
        mock_project = mocker.MagicMock()
        mock_project.name = "Watson"
        mock_project.is_active = True
        mock_project.uploads = mocker.MagicMock()
        mock_project.uploads.order_by.return_value = []

        mock_query = mocker.MagicMock()
        mock_query.filter.return_value.first_or_404.return_value = mock_project

        mocker.patch("jazzband.projects.views.Project.query", mock_query)

        response = client.get("/projects/Watson", follow_redirects=False)

        assert response.status_code != 301


def test_uppercase_url_redirects_to_canonical(app, mocker):
    """/projects/WATSON should redirect to canonical /projects/Watson."""
    with app.test_client() as client:
        mock_project = mocker.MagicMock()
        mock_project.name = "Watson"
        mock_project.is_active = True

        mock_query = mocker.MagicMock()
        mock_query.filter.return_value.first_or_404.return_value = mock_project

        mocker.patch("jazzband.projects.views.Project.query", mock_query)

        response = client.get("/projects/WATSON", follow_redirects=False)

        assert response.status_code == 301
        assert "/projects/Watson" in response.headers["Location"]


def test_hyphen_underscore_normalization(app, mocker):
    """/projects/some_project should redirect to canonical /projects/some-project."""
    with app.test_client() as client:
        mock_project = mocker.MagicMock()
        mock_project.name = "some-project"
        mock_project.is_active = True

        mock_query = mocker.MagicMock()
        mock_query.filter.return_value.first_or_404.return_value = mock_project

        mocker.patch("jazzband.projects.views.Project.query", mock_query)

        response = client.get("/projects/some_project", follow_redirects=False)

        assert response.status_code == 301
        assert "/projects/some-project" in response.headers["Location"]
