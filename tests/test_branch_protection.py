"""Default-branch history protection without changing member write access."""

import json

import pytest
from requests import HTTPError
from spinach import AbortException

from jazzband.account.blueprint import GitHubBlueprint
from jazzband.hooks import repository
from jazzband.projects import tasks as project_tasks


def api_response(mocker, data, *, links=None, error=None):
    response = mocker.Mock()
    response.json.return_value = data
    response.links = links or {}
    response.raise_for_status.side_effect = error
    return response


@pytest.fixture
def protection_api(github_blueprint, mocker):
    blueprint, session = github_blueprint
    repo = {
        "archived": False,
        "default_branch": "main",
        "owner": {"login": "TEST-ORG-NAME"},
    }
    session.get.side_effect = [
        api_response(mocker, repo),
        api_response(mocker, []),
    ]
    session.post.return_value = api_response(mocker, {"id": 42})
    return blueprint, session, repo


def protect(blueprint):
    return GitHubBlueprint.ensure_default_branch_history_protection(
        blueprint, "test-project"
    )


def test_missing_protection_creates_only_default_branch_rule(protection_api):
    blueprint, session, _ = protection_api

    assert protect(blueprint) is True

    session.post.assert_called_once_with(
        "repos/test-org-name/test-project/rulesets",
        json={
            "name": "Protect default branch history",
            "target": "branch",
            "enforcement": "active",
            "bypass_actors": [],
            "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
            "rules": [{"type": "non_fast_forward"}],
        },
    )
    session.post.return_value.raise_for_status.assert_called_once()
    session.put.assert_not_called()
    session.patch.assert_not_called()
    session.delete.assert_not_called()


@pytest.mark.parametrize("source_type", ["Repository", "Organization"])
def test_reuses_effective_rule_with_additional_protections(
    protection_api, mocker, source_type
):
    blueprint, session, repo = protection_api
    session.get.side_effect = [
        api_response(mocker, repo),
        api_response(
            mocker,
            [
                {"type": "deletion", "ruleset_id": 17},
                {
                    "type": "non_fast_forward",
                    "ruleset_id": 17,
                    "ruleset_source_type": source_type,
                },
            ],
        ),
        api_response(
            mocker,
            {
                "enforcement": "active",
                "bypass_actors": [],
                "rules": [{"type": "deletion"}, {"type": "non_fast_forward"}],
            },
        ),
    ]

    assert protect(blueprint) is True

    session.get.assert_any_call("repos/test-org-name/test-project/rulesets/17")
    session.post.assert_not_called()
    session.put.assert_not_called()
    session.patch.assert_not_called()
    session.delete.assert_not_called()


def test_checks_later_rule_pages_before_creating(protection_api, mocker):
    blueprint, session, repo = protection_api
    next_page = (
        "https://api.github.com/repos/test-org-name/test-project/"
        "rules/branches/main?per_page=100&page=2"
    )
    session.get.side_effect = [
        api_response(mocker, repo),
        api_response(mocker, [], links={"next": {"url": next_page}}),
        api_response(mocker, [{"type": "non_fast_forward", "ruleset_id": 17}]),
        api_response(mocker, {"enforcement": "active", "bypass_actors": []}),
    ]

    assert protect(blueprint) is True

    session.get.assert_any_call(next_page)
    session.post.assert_not_called()


def test_rule_with_bypass_does_not_satisfy_protection(protection_api, mocker):
    blueprint, session, repo = protection_api
    session.get.side_effect = [
        api_response(mocker, repo),
        api_response(mocker, [{"type": "non_fast_forward", "ruleset_id": 17}]),
        api_response(
            mocker,
            {
                "enforcement": "active",
                "bypass_actors": [{"actor_type": "Team", "actor_id": 1}],
            },
        ),
    ]

    assert protect(blueprint) is True

    session.post.assert_called_once()
    session.put.assert_not_called()
    session.patch.assert_not_called()
    session.delete.assert_not_called()


def test_unreadable_bypass_permissions_abort_without_mutation(protection_api, mocker):
    blueprint, session, repo = protection_api
    session.get.side_effect = [
        api_response(mocker, repo),
        api_response(mocker, [{"type": "non_fast_forward", "ruleset_id": 17}]),
        api_response(mocker, {"enforcement": "active"}),
    ]

    with pytest.raises(RuntimeError, match="Cannot verify ruleset bypass"):
        protect(blueprint)

    session.post.assert_not_called()


def test_rule_lookup_failure_aborts_without_creation(protection_api, mocker):
    blueprint, session, repo = protection_api
    session.get.side_effect = [
        api_response(mocker, repo),
        api_response(mocker, {}, error=HTTPError("rules unavailable")),
    ]

    with pytest.raises(HTTPError, match="rules unavailable"):
        protect(blueprint)

    session.post.assert_not_called()


def test_creation_failure_is_propagated(protection_api):
    blueprint, session, _ = protection_api
    session.post.return_value.raise_for_status.side_effect = HTTPError("create failed")

    with pytest.raises(HTTPError, match="create failed"):
        protect(blueprint)


def test_archived_repository_is_not_modified(protection_api, mocker):
    blueprint, session, repo = protection_api
    repo["archived"] = True
    session.get.side_effect = [api_response(mocker, repo)]

    assert protect(blueprint) is False

    assert session.get.call_count == 1
    session.post.assert_not_called()


def test_default_branch_name_is_encoded(protection_api, mocker):
    blueprint, session, repo = protection_api
    repo["default_branch"] = "release/current"
    session.get.side_effect = [
        api_response(mocker, repo),
        api_response(mocker, []),
    ]

    protect(blueprint)

    session.get.assert_any_call(
        "repos/test-org-name/test-project/rules/branches/release%2Fcurrent?per_page=100"
    )


def test_protection_task_serializes_repository_changes(mocker):
    redis = mocker.patch("jazzband.projects.tasks.redis")
    github = mocker.patch("jazzband.projects.tasks.github", new=mocker.Mock())
    github.ensure_default_branch_history_protection.return_value = True

    assert project_tasks.protect_default_branch("test-project") is True

    redis.lock.assert_called_once_with(
        "protect-default-branch-test-project", ttl=project_tasks.ONE_MINUTE * 5
    )
    github.ensure_default_branch_history_protection.assert_called_once_with(
        "test-project"
    )


def test_periodic_sync_reconciles_nonarchived_repositories(mocker):
    mocker.patch("jazzband.projects.tasks.redis")
    github = mocker.patch("jazzband.projects.tasks.github", new=mocker.Mock())
    project = mocker.patch("jazzband.projects.tasks.Project")
    schedule = mocker.patch.object(project_tasks.tasks, "schedule")
    projects = [
        {"name": "active", "archived": False},
        {"name": "site-inactive", "archived": False, "is_active": False},
        {"name": "archived", "archived": True},
    ]
    github.get_projects.return_value = projects

    project_tasks.sync_projects()

    project.sync.assert_called_once_with(projects)
    assert schedule.call_args_list == [
        mocker.call(project_tasks.protect_default_branch, "active"),
        mocker.call(project_tasks.protect_default_branch, "site-inactive"),
    ]


@pytest.mark.parametrize("protection_result", [False, HTTPError("protection failed")])
def test_onboarding_does_not_grant_write_without_protection(mocker, protection_result):
    redis = mocker.patch("jazzband.projects.tasks.redis")
    redis.get.return_value = json.dumps({"repository": {"name": "test-project"}})
    project = mocker.patch("jazzband.projects.tasks.Project")
    github = mocker.patch("jazzband.projects.tasks.github", new=mocker.Mock())
    protection = mocker.patch("jazzband.projects.tasks.protect_default_branch")
    if isinstance(protection_result, Exception):
        protection.side_effect = protection_result
        with pytest.raises(HTTPError, match="protection failed"):
            project_tasks.update_project_by_hook("hook-id")
    else:
        protection.return_value = protection_result
        with pytest.raises(AbortException, match="archived before onboarding"):
            project_tasks.update_project_by_hook("hook-id")

    project.sync.assert_not_called()
    github.enable_issues.assert_not_called()
    github.add_repo_to_team.assert_not_called()


def test_onboarding_protects_before_preserving_member_write_grant(
    test_app_context, mocker
):
    redis = mocker.patch("jazzband.projects.tasks.redis")
    redis.get.return_value = json.dumps({"repository": {"name": "test-project"}})
    project = mocker.patch("jazzband.projects.tasks.Project")
    project.query.filter.return_value.first.return_value.name = "test-project"
    github = mocker.patch("jazzband.projects.tasks.github", new=mocker.Mock())
    github.members_team_slug = "members"
    github.add_repo_to_team.return_value.status_code = 204
    protection = mocker.patch(
        "jazzband.projects.tasks.protect_default_branch", return_value=True
    )
    calls = mocker.Mock()
    calls.attach_mock(protection, "protect")
    calls.attach_mock(github.add_repo_to_team, "grant")

    project_tasks.update_project_by_hook("hook-id")

    assert calls.mock_calls == [
        mocker.call.protect("test-project"),
        mocker.call.grant("members", "test-project", "push"),
    ]


def test_unarchive_schedules_only_protection(test_app_context, mocker):
    schedule = mocker.patch("jazzband.hooks.spinach", new=mocker.Mock()).schedule

    repository(
        {
            "action": "unarchived",
            "repository": {
                "name": "test-project",
                "owner": {"login": "TEST-ORG-NAME"},
            },
        },
        "id",
    )

    schedule.assert_called_once_with(
        project_tasks.protect_default_branch, "test-project"
    )


@pytest.mark.parametrize("action", ["created", "transferred"])
def test_onboarding_events_keep_existing_task(action, test_app_context, mocker):
    schedule = mocker.patch("jazzband.hooks.spinach", new=mocker.Mock()).schedule

    payload = {
        "action": action,
        "repository": {
            "name": "test-project",
            "owner": {"login": "test-org-name"},
        },
    }
    repository(payload, "id")

    schedule.assert_called_once_with(
        project_tasks.update_project_by_hook, mocker.ANY, payload
    )


def test_other_repository_events_do_not_schedule_protection(mocker):
    schedule = mocker.patch("jazzband.hooks.spinach", new=mocker.Mock()).schedule

    repository({"action": "edited", "repository": {"name": "test-project"}}, "id")

    schedule.assert_not_called()


@pytest.mark.parametrize("action", ["created", "transferred", "unarchived"])
@pytest.mark.parametrize("owner", [{}, {"login": "another-org"}])
def test_repository_hook_rejects_other_or_missing_owner(
    action, owner, test_app_context, mocker
):
    schedule = mocker.patch("jazzband.hooks.spinach", new=mocker.Mock()).schedule

    repository(
        {
            "action": action,
            "repository": {"name": "test-project", "owner": owner},
        },
        "id",
    )

    schedule.assert_not_called()


def test_onboarding_retry_keeps_payload_and_resumes_after_protection(
    test_app_context, mocker
):
    redis = mocker.patch("jazzband.projects.tasks.redis")
    project = mocker.patch("jazzband.projects.tasks.Project")
    project.query.filter.return_value.first.return_value.name = "test-project"
    github = mocker.patch("jazzband.projects.tasks.github", new=mocker.Mock())
    github.members_team_slug = "members"
    github.add_repo_to_team.return_value.status_code = 204
    protection = mocker.patch(
        "jazzband.projects.tasks.protect_default_branch",
        side_effect=[HTTPError("protection failed"), True],
    )
    payload = {"repository": {"name": "test-project"}}

    with pytest.raises(HTTPError, match="protection failed"):
        project_tasks.update_project_by_hook("hook-id", payload)
    github.add_repo_to_team.assert_not_called()

    project_tasks.update_project_by_hook("hook-id", payload)

    redis.get.assert_not_called()
    assert protection.call_count == 2
    github.add_repo_to_team.assert_called_once_with("members", "test-project", "push")
    assert project_tasks.tasks.get("update_project_by_hook").max_retries == 3


def test_missing_legacy_onboarding_payload_fails_visibly(mocker):
    redis = mocker.patch("jazzband.projects.tasks.redis")
    redis.get.return_value = None
    protection = mocker.patch("jazzband.projects.tasks.protect_default_branch")

    with pytest.raises(AbortException, match="onboarding payload unavailable"):
        project_tasks.update_project_by_hook("expired-hook-id")

    protection.assert_not_called()


def test_onboarding_failure_after_protection_does_not_retry(mocker):
    mocker.patch("jazzband.projects.tasks.protect_default_branch", return_value=True)
    onboarding = mocker.patch(
        "jazzband.projects.tasks._onboard_project",
        side_effect=HTTPError("issue created but save failed"),
    )
    payload = {"repository": {"name": "test-project"}}

    with pytest.raises(
        AbortException, match="onboarding failed after protection"
    ) as exc:
        project_tasks.update_project_by_hook("hook-id", payload)

    onboarding.assert_called_once_with(payload)
    assert isinstance(exc.value.__cause__, HTTPError)


@pytest.mark.parametrize("archived", [False, True])
@pytest.mark.parametrize("owner", [{}, {"login": "new-owner"}])
def test_live_repository_owner_is_checked_before_any_ruleset_request(
    protection_api, mocker, archived, owner
):
    blueprint, session, repo = protection_api
    repo["owner"] = owner
    repo["archived"] = archived
    session.get.side_effect = [api_response(mocker, repo)]

    with pytest.raises(RuntimeError, match="not in the configured organization"):
        protect(blueprint)

    assert session.get.call_count == 1
    session.post.assert_not_called()
    session.put.assert_not_called()
    session.patch.assert_not_called()
    session.delete.assert_not_called()


def test_archive_before_queued_onboarding_fails_visibly_without_side_effects(
    protection_api, mocker
):
    blueprint, session, repo = protection_api
    repo["archived"] = True
    session.get.side_effect = [api_response(mocker, repo)]
    mocker.patch("jazzband.projects.tasks.redis")
    mocker.patch("jazzband.projects.tasks.github", new=blueprint)
    blueprint.ensure_default_branch_history_protection.side_effect = lambda repo_name: (
        protect(blueprint)
    )
    onboarding = mocker.patch("jazzband.projects.tasks._onboard_project")
    payload = {"repository": {"name": "test-project", "archived": False}}

    with pytest.raises(AbortException, match="Unarchive and redeliver"):
        project_tasks.update_project_by_hook("queued-hook", payload)

    onboarding.assert_not_called()
    session.post.assert_not_called()
    assert session.get.call_count == 1
