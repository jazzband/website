import json

from jazzband.projects.tasks import update_project_by_hook
from jazzband.tasks import JazzbandSpinach


def post(client, hook, data, guid="abc"):
    headers = {"X-GitHub-Event": hook, "X-GitHub-Delivery": guid}
    return client.post(
        "/hooks",
        content_type="application/json",
        data=json.dumps(data),
        headers=headers,
    )


def test_ping(client):
    rv = post(client, "ping", {})
    assert b"pong" in rv.data
    assert rv.status_code == 200


def test_repo_transferred_hook(client, datadir, mocker):
    contents = (datadir / "repository.json").read_text()
    mocked_schedule = mocker.patch.object(JazzbandSpinach, "schedule")
    response = post(client, "repository", json.loads(contents))
    assert response.data
    response_string = response.data.decode("utf-8")
    assert response_string.startswith("repo-added-")
    mocked_schedule.assert_called_once_with(update_project_by_hook, response_string)
    #better but needs more strugle
