"""
Tests for the projects index page functionality, including the leads filter.
"""

from flask import url_for


def test_projects_index_default_shows_all_projects(app, mocker):
    """Test that projects index shows all projects by default."""
    with app.test_client() as client:
        # Mock the project query to return some test projects
        mock_projects = mocker.MagicMock()
        mock_projects.count.return_value = 3

        # Use mocker.patch instead of unittest.mock
        mock_query = mocker.patch("jazzband.projects.views.Project.query")
        mock_query.filter.return_value.order_by.return_value = mock_projects

        response = client.get(url_for("projects.index"))

        assert response.status_code == 200
        # Check that the default filter is 'all'
        assert b"leads=all" not in response.data  # Default should not have filter param
        assert b"All projects" in response.data


def test_projects_index_filter_with_leads(app, mocker):
    """Test that projects index can filter projects with leads."""
    with app.test_client() as client:
        # Mock the project query to return projects with leads
        mock_projects = mocker.MagicMock()
        mock_projects.count.return_value = 2

        # Use mocker.patch for proper mocking
        mock_query = mocker.patch("jazzband.projects.views.Project.query")
        mock_filter = mocker.MagicMock()
        mock_join = mocker.MagicMock()
        mock_group_by = mocker.MagicMock()

        # Setup the mock chain for with_leads filter
        mock_query.filter.return_value = mock_filter
        mock_filter.join.return_value = mock_join
        mock_join.filter.return_value = mock_join
        mock_join.group_by.return_value = mock_group_by
        mock_group_by.order_by.return_value = mock_projects

        response = client.get(url_for("projects.index", leads="yes"))

        assert response.status_code == 200
        assert b"leads=yes" in response.data
        assert b"With leads" in response.data


def test_projects_index_filter_without_leads(app, mocker):
    """Test that projects index can filter projects without leads."""
    with app.test_client() as client:
        # Mock the project query to return projects without leads
        mock_projects = mocker.MagicMock()
        mock_projects.count.return_value = 1

        # Use mocker.patch for proper mocking
        mock_query = mocker.patch("jazzband.projects.views.Project.query")
        mock_filter = mocker.MagicMock()
        mock_subquery = mocker.MagicMock()
        mock_final_filter = mocker.MagicMock()

        # Setup the mock chain for without_leads filter
        mock_query.filter.return_value = mock_filter
        mock_query.join.return_value = mock_subquery
        mock_subquery.filter.return_value = mock_subquery
        mock_subquery.subquery.return_value = mock_subquery
        mock_subquery.select.return_value = mock_subquery
        mock_subquery.with_only_columns.return_value = mock_subquery
        mock_filter.filter.return_value = mock_final_filter
        mock_final_filter.order_by.return_value = mock_projects

        response = client.get(url_for("projects.index", leads="no"))

        assert response.status_code == 200
        assert b"leads=no" in response.data
        assert b"Without leads" in response.data


def test_projects_index_filter_preserves_sorting(app, mocker):
    """Test that projects index filter preserves existing sorting parameters."""
    with app.test_client() as client:
        # Mock the project query
        mock_projects = mocker.MagicMock()
        mock_projects.count.return_value = 2

        # Use mocker.patch for proper mocking
        mock_query = mocker.patch("jazzband.projects.views.Project.query")
        mock_filter = mocker.MagicMock()
        mock_join = mocker.MagicMock()
        mock_group_by = mocker.MagicMock()

        mock_query.filter.return_value = mock_filter
        mock_filter.join.return_value = mock_join
        mock_join.filter.return_value = mock_join
        mock_join.group_by.return_value = mock_group_by
        mock_group_by.order_by.return_value = mock_projects

        # Test with sorting parameters
        response = client.get(
            url_for("projects.index", leads="yes", sorter="members", order="asc")
        )

        assert response.status_code == 200
        # Check that the filter links preserve sorting parameters
        assert b"leads=yes&sorter=members&order=asc" in response.data


def test_projects_index_filter_active_states(app, mocker):
    """Test that projects index shows correct active filter states."""
    with app.test_client() as client:
        # Mock the project query
        mock_projects = mocker.MagicMock()
        mock_projects.count.return_value = 3

        # Use mocker.patch for proper mocking
        mock_query = mocker.patch("jazzband.projects.views.Project.query")
        mock_query.filter.return_value.order_by.return_value = mock_projects

        # Test default (all projects)
        response = client.get(url_for("projects.index"))
        assert (
            b'class="active"' in response.data
        )  # All projects should be active by default

        # Test with_leads filter
        mock_filter = mocker.MagicMock()
        mock_join = mocker.MagicMock()
        mock_group_by = mocker.MagicMock()

        mock_query.filter.return_value = mock_filter
        mock_filter.join.return_value = mock_join
        mock_join.filter.return_value = mock_join
        mock_join.group_by.return_value = mock_group_by
        mock_group_by.order_by.return_value = mock_projects

        response = client.get(url_for("projects.index", leads="yes"))
        assert b'leads=yes" class="active"' in response.data

        # Test without_leads filter
        mock_subquery = mocker.MagicMock()
        mock_final_filter = mocker.MagicMock()

        mock_query.filter.return_value = mock_filter
        mock_query.join.return_value = mock_subquery
        mock_subquery.filter.return_value = mock_subquery
        mock_subquery.subquery.return_value = mock_subquery
        mock_subquery.select.return_value = mock_subquery
        mock_subquery.with_only_columns.return_value = mock_subquery
        mock_filter.filter.return_value = mock_final_filter
        mock_final_filter.order_by.return_value = mock_projects

        response = client.get(url_for("projects.index", leads="no"))
        assert b'leads=no" class="active"' in response.data
