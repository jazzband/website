from types import SimpleNamespace

import pytest

from jazzband.projects import commands, tasks


@pytest.fixture
def members_team_api(mocker):
    github = mocker.patch("jazzband.projects.tasks.github", new=mocker.Mock())
    github.members_team_slug = "members"
    github.get_team_repos.return_value = []
    github.add_repo_to_team.return_value.status_code = 204
    project = mocker.patch("jazzband.projects.tasks.Project")
    project.query.filter_by.return_value.all.return_value = [
        SimpleNamespace(id=1, name="test-project")
    ]
    return github


@pytest.mark.parametrize(
    ("command", "args"),
    [
        (commands.add_repo_to_members_team, ["test-project"]),
        (commands.update_all_projects_members_team, []),
    ],
)
def test_members_team_commands_default_to_read(app, members_team_api, command, args):
    result = app.test_cli_runner().invoke(command, args)

    assert result.exit_code == 0, result.output
    members_team_api.add_repo_to_team.assert_called_once_with(
        "members", "test-project", "pull"
    )


@pytest.mark.parametrize(
    ("task", "args"),
    [
        (tasks.add_repo_to_members_team, ["test-project"]),
        (tasks.update_all_projects_members_team, []),
    ],
)
def test_members_team_tasks_default_to_read(members_team_api, task, args):
    task(*args)

    members_team_api.add_repo_to_team.assert_called_once_with(
        "members", "test-project", "pull"
    )


@pytest.mark.parametrize("existing_role", ["triage", "push", "maintain", "admin"])
def test_bulk_read_downgrades_stronger_access(members_team_api, existing_role):
    members_team_api.get_team_repos.return_value = [
        {
            "name": "test-project",
            "permissions": {"pull": True, existing_role: True},
        }
    ]

    tasks.update_all_projects_members_team("pull")

    members_team_api.add_repo_to_team.assert_called_once_with(
        "members", "test-project", "pull"
    )


@pytest.mark.parametrize("permission", ["pull", "push", "maintain", "admin"])
def test_bulk_skips_exact_existing_access(members_team_api, permission):
    members_team_api.get_team_repos.return_value = [
        {
            "name": "test-project",
            "permissions": {"pull": True, permission: True},
        }
    ]

    tasks.update_all_projects_members_team(permission)

    members_team_api.add_repo_to_team.assert_not_called()


@pytest.mark.parametrize(
    ("command", "args"),
    [
        (commands.add_repo_to_members_team, ["test-project"]),
        (commands.update_all_projects_members_team, []),
    ],
)
@pytest.mark.parametrize("permission", ["push", "maintain", "admin"])
def test_members_team_commands_preserve_explicit_access(
    app, members_team_api, command, args, permission
):
    result = app.test_cli_runner().invoke(command, [*args, "--permission", permission])

    assert result.exit_code == 0, result.output
    members_team_api.add_repo_to_team.assert_called_once_with(
        "members", "test-project", permission
    )
