"""Tests for the project list and its sorting controls."""

from html.parser import HTMLParser
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

from flask import url_for
import pytest


@pytest.fixture
def listed_projects(mocker):
    projects = [
        SimpleNamespace(
            name=name,
            description=f"Description of {name}",
            membership_count=2,
            uploads_count=1,
            subscribers_count=0,
            stargazers_count=0,
            forks_count=0,
            open_issues_count=0,
        )
        for name in ["example-project", "another-project"]
    ]
    results = mocker.MagicMock()
    results.count.return_value = len(projects)
    results.__iter__.return_value = iter(projects)
    query = mocker.patch("jazzband.projects.views.Project.query")
    query.filter.return_value.order_by.return_value = results
    return projects


class LinkParser(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.links = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.links.append(dict(attrs))


def test_projects_index_renders_projects(app, listed_projects):
    with app.test_client() as client:
        response = client.get(url_for("projects.index"))

        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "The following 2 Jazzband projects" in html
        links = {link.get("href") for link in LinkParser(html).links}
        for project in listed_projects:
            assert url_for("projects.detail", name=project.name) in links
            assert f">{project.name}</a>" in html
            assert project.description in html


@pytest.mark.parametrize(
    ("query", "selected", "next_order"),
    [
        ({}, "random", None),
        ({"sorter": "name"}, "name", "desc"),
        ({"sorter": "members", "order": "desc"}, "members", None),
        ({"sorter": "unknown"}, "random", None),
    ],
)
def test_projects_index_sorting_controls(
    app, listed_projects, query, selected, next_order
):
    with app.test_client() as client:
        response = client.get(url_for("projects.index", **query))

    assert response.status_code == 200
    links = LinkParser(response.get_data(as_text=True)).links
    selected_links = [
        link
        for link in links
        if link.get("title", "").startswith("Sort by ")
        and "red" in link.get("class", "").split()
    ]
    assert len(selected_links) == 1
    link = selected_links[0]
    assert link["title"] == f"Sort by {selected}"
    expected_query = {"sorter": [selected]}
    if next_order is not None:
        expected_query["order"] = [next_order]
    assert parse_qs(urlsplit(link["href"]).query) == expected_query
