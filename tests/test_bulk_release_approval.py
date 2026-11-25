"""A bulk approval must authorize exactly the files the lead reviewed."""

import hashlib
from html.parser import HTMLParser
from pathlib import Path
import shlex
import shutil
from types import SimpleNamespace

from flask import render_template
import pytest

from jazzband.projects import forms, views


@pytest.fixture
def release_case(app, mocker, tmp_path):
    app.config.update(SECRET_KEY="bulk-release-test-key", RELEASE_ENABLED=True)
    user = SimpleNamespace(id=7, has_2fa=True)
    mocker.patch.object(forms, "current_user", user)
    mocker.patch.object(views, "current_user", user)
    uploads = []
    project = SimpleNamespace(
        id=11,
        name="test-project",
        pypi_json_url="https://pypi.org/pypi/test-project/json",
        current_user_is_lead=True,
    )

    class UploadQuery:
        def __init__(self, filters=None, released=False):
            self.filters = filters or {}
            self.released = released

        def filter_by(self, **filters):
            return UploadQuery({**self.filters, **filters}, self.released)

        def filter(self, expression):
            return UploadQuery(self.filters, released=True)

        def all(self):
            return [
                upload
                for upload in uploads
                if all(
                    getattr(upload, key) == value for key, value in self.filters.items()
                )
                and (not self.released or upload.released_at is not None)
            ]

    project.uploads = UploadQuery()
    view = views.BulkReleaseView()
    view.project = project

    def add_upload(filename, content):
        path = tmp_path / filename
        path.write_bytes(content)
        upload = SimpleNamespace(
            id=len(uploads) + 1,
            project=project,
            project_id=project.id,
            filename=filename,
            version="1.0.0",
            size=len(content),
            sha256_digest=hashlib.sha256(content).hexdigest(),
            md5_digest=hashlib.md5(content).hexdigest(),
            full_path=str(path),
            released_at=None,
            save=mocker.Mock(),
        )
        uploads.append(upload)
        return upload

    add_upload("test-project-1.0.0.tar.gz", b"reviewed source archive")
    add_upload("test-project-1.0.0-py3-none-any.whl", b"reviewed wheel")
    response = mocker.Mock()
    response.json.return_value = {"releases": {}}
    pypi = mocker.patch.object(views.requests, "get", return_value=response)
    sent = []

    def publish(command):
        args = shlex.split(command)
        assert args[:2] == ["twine", "upload"]
        sent.append({Path(path).name: Path(path).read_bytes() for path in args[2:]})
        return SimpleNamespace(return_code=0, out="uploaded", err="")

    twine = mocker.patch.object(views.delegator, "run", side_effect=publish)

    def confirmation():
        with app.test_request_context("/projects/test-project/release/1.0.0"):
            context = view.get(project.name, "1.0.0")
            form = context["bulk_release_form"]
            token = getattr(form, "approval_token", None)
            return token.data if token is not None else ""

    def submit(token, version="1.0.0", **data):
        with app.test_request_context(
            f"/projects/{project.name}/release/{version}",
            method="POST",
            data={"project_name": project.name, "approval_token": token, **data},
        ):
            return view.post(project.name, version)

    return SimpleNamespace(
        app=app,
        user=user,
        project=project,
        view=view,
        uploads=uploads,
        add_upload=add_upload,
        confirmation=confirmation,
        submit=submit,
        pypi=pypi,
        twine=twine,
        sent=sent,
    )


def test_upload_added_after_confirmation_is_not_released(release_case):
    token = release_case.confirmation()
    release_case.add_upload("test-project-1.0.0-extra.whl", b"unreviewed wheel")

    release_case.submit(token)

    assert release_case.sent == []
    assert all(upload.released_at is None for upload in release_case.uploads)
    release_case.pypi.assert_not_called()


@pytest.mark.parametrize("change", ["remove", "replace", "rename", "digest", "size"])
def test_changed_upload_details_invalidate_confirmation(release_case, change):
    token = release_case.confirmation()
    upload = release_case.uploads[0]
    if change == "remove":
        release_case.uploads.pop()
    elif change == "replace":
        upload.id = 99
    elif change == "rename":
        upload.filename = "test-project-1.0.0-renamed.tar.gz"
    elif change == "digest":
        upload.sha256_digest = "0" * 64
    else:
        upload.size += 1

    release_case.submit(token)

    assert release_case.sent == []
    assert all(upload.released_at is None for upload in release_case.uploads)
    release_case.pypi.assert_not_called()


@pytest.mark.parametrize("invalid_token", ["", "not-a-signed-confirmation"])
def test_unverified_confirmation_cannot_release_files(release_case, invalid_token):
    release_case.submit(invalid_token)

    assert release_case.sent == []
    assert all(upload.released_at is None for upload in release_case.uploads)
    release_case.pypi.assert_not_called()


def test_tampered_confirmation_cannot_release_files(release_case):
    token = release_case.confirmation()

    release_case.submit(token + "tampered")

    assert release_case.sent == []
    release_case.pypi.assert_not_called()


@pytest.mark.parametrize("change", ["user", "project", "version"])
def test_confirmation_cannot_authorize_another_release(release_case, change):
    token = release_case.confirmation()
    version = "1.0.0"
    if change == "user":
        release_case.user.id = 8
    elif change == "project":
        release_case.project.id = 12
    else:
        version = "2.0.0"
        for upload in release_case.uploads:
            upload.version = version

    release_case.submit(token, version=version)

    assert release_case.sent == []
    release_case.pypi.assert_not_called()


def test_unchanged_approval_releases_exact_reviewed_bytes(release_case):
    token = release_case.confirmation()

    result = release_case.submit(token)

    assert result.status_code == 302
    assert release_case.sent == [
        {
            "test-project-1.0.0.tar.gz": b"reviewed source archive",
            "test-project-1.0.0-py3-none-any.whl": b"reviewed wheel",
        }
    ]
    assert all(upload.released_at is not None for upload in release_case.uploads)


def test_upload_order_does_not_invalidate_confirmation(release_case):
    token = release_case.confirmation()
    release_case.uploads.reverse()

    release_case.submit(token)

    assert len(release_case.sent) == 1
    assert all(upload.released_at is not None for upload in release_case.uploads)


@pytest.mark.parametrize("change", ["same-size", "different-size", "missing"])
def test_changed_stored_bytes_block_the_entire_release(release_case, change):
    token = release_case.confirmation()
    upload = release_case.uploads[-1]
    path = Path(upload.full_path)
    if change == "same-size":
        path.write_bytes(b"x" * upload.size)
    elif change == "different-size":
        path.write_bytes(b"short")
    else:
        path.unlink()

    release_case.submit(token)

    assert release_case.sent == []
    assert all(upload.released_at is None for upload in release_case.uploads)


def test_copied_bytes_are_checked_before_twine(release_case, mocker):
    token = release_case.confirmation()
    original_copy = shutil.copy

    def corrupt_copy(source, destination):
        result = original_copy(source, destination)
        copied = Path(destination)
        copied.write_bytes(b"x" * copied.stat().st_size)
        return result

    mocker.patch.object(views.shutil, "copy", side_effect=corrupt_copy)

    release_case.submit(token)

    assert release_case.sent == []
    assert all(upload.released_at is None for upload in release_case.uploads)


def test_confirmation_does_not_bypass_two_factor_auth(release_case):
    token = release_case.confirmation()
    release_case.user.has_2fa = False

    release_case.submit(token)

    assert release_case.sent == []
    release_case.pypi.assert_not_called()


def test_confirmation_does_not_bypass_project_name_check(release_case):
    token = release_case.confirmation()

    release_case.submit(token, project_name="different-project")

    assert release_case.sent == []
    release_case.pypi.assert_not_called()


def test_new_confirmation_allows_reviewed_added_upload(release_case):
    old_token = release_case.confirmation()
    release_case.add_upload("test-project-1.0.0-extra.whl", b"newly reviewed wheel")
    release_case.submit(old_token)
    assert release_case.sent == []

    release_case.submit(release_case.confirmation())

    assert release_case.sent == [
        {
            "test-project-1.0.0.tar.gz": b"reviewed source archive",
            "test-project-1.0.0-py3-none-any.whl": b"reviewed wheel",
            "test-project-1.0.0-extra.whl": b"newly reviewed wheel",
        }
    ]


def test_successful_confirmation_cannot_release_again(release_case):
    token = release_case.confirmation()
    release_case.submit(token)

    release_case.submit(token)

    assert len(release_case.sent) == 1


def test_confirmation_does_not_bypass_csrf(release_case):
    token = release_case.confirmation()
    release_case.app.config["WTF_CSRF_ENABLED"] = True

    release_case.submit(token)

    assert release_case.sent == []
    release_case.pypi.assert_not_called()


def test_confirmation_page_submits_approval_with_displayed_files(release_case):
    class ApprovalInput(HTMLParser):
        token = None

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == "input" and attrs.get("name") == "approval_token":
                self.token = attrs.get("value")
                assert attrs.get("type") == "hidden"

    with release_case.app.test_request_context("/projects/test-project/release/1.0.0"):
        context = release_case.view.get(release_case.project.name, "1.0.0")
        page = render_template("projects/bulk_release.html", **context)

    parser = ApprovalInput()
    parser.feed(page)
    assert parser.token
    for upload in release_case.uploads:
        assert upload.filename in page
        assert upload.sha256_digest in page
    release_case.submit(parser.token)
    assert len(release_case.sent) == 1
