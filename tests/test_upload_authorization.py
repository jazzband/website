"""Authorization for individual staged distribution actions."""

import re

from flask_login import login_user
from flask_sqlalchemy.query import Query
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from werkzeug.exceptions import NotFound

from jazzband.db import postgres
from jazzband.members.models import User
from jazzband.projects.models import Project, ProjectMembership
from jazzband.projects.views import (
    UploadDeleteView,
    UploadDownloadView,
    UploadReleaseView,
)


@pytest.fixture
def upload_authorization_db(app, mocker):
    engine = create_engine("sqlite://")
    with app.app_context(), engine.connect() as connection:
        connection.connection.driver_connection.create_function(
            "normalize_pep426_name",
            1,
            lambda value: re.sub(r"[-_.]+", "-", value.lower()),
        )
        postgres.metadata.create_all(
            connection,
            tables=[User.__table__, Project.__table__, ProjectMembership.__table__],
        )
        connection.execute(
            User.__table__.insert(),
            [
                {
                    "id": user_id,
                    "login": f"user-{user_id}",
                    "is_member": True,
                    "is_roadie": user_id in (5, 6),
                }
                for user_id in range(1, 7)
            ],
        )
        connection.execute(
            Project.__table__.insert(),
            [
                {"id": 1, "name": "test-project", "is_active": True},
                {"id": 2, "name": "other-project", "is_active": True},
            ],
        )
        connection.execute(
            ProjectMembership.__table__.insert(),
            [
                {"user_id": 1, "project_id": 1, "is_lead": False},
                {"user_id": 2, "project_id": 1, "is_lead": True},
                {"user_id": 3, "project_id": 1, "is_lead": False},
                {"user_id": 3, "project_id": 2, "is_lead": True},
                {"user_id": 5, "project_id": 1, "is_lead": False},
            ],
        )
        with Session(bind=connection, query_cls=Query) as session:
            mocker.patch.object(Project, "query", session.query(Project))
            yield session
    engine.dispose()


@pytest.mark.parametrize("view_class", [UploadReleaseView, UploadDeleteView])
@pytest.mark.parametrize(
    ("user_id", "active", "allowed"),
    [
        pytest.param(1, True, False, id="member-with-different-lead"),
        pytest.param(3, True, False, id="lead-of-another-project"),
        pytest.param(4, True, False, id="nonmember"),
        pytest.param(2, True, True, id="project-lead"),
        pytest.param(5, True, True, id="member-roadie"),
        pytest.param(6, True, False, id="nonmember-roadie"),
        pytest.param(2, False, False, id="inactive-project-lead"),
        pytest.param(5, False, False, id="inactive-project-roadie"),
    ],
)
def test_single_upload_action_requires_current_users_lead_role(
    app, upload_authorization_db, view_class, user_id, active, allowed
):
    session = upload_authorization_db
    session.execute(
        Project.__table__.update().where(Project.id == 1).values(is_active=active)
    )
    with app.test_request_context():
        login_user(session.get(User, user_id))
        project = view_class().project_query("test-project").first()
    assert (project.id if project else None) == (1 if allowed else None)


@pytest.mark.parametrize("view_class", [UploadReleaseView, UploadDeleteView])
@pytest.mark.parametrize("method", ["GET", "POST"])
def test_nonlead_member_cannot_reach_upload_action_handler(
    app, upload_authorization_db, mocker, monkeypatch, view_class, method
):
    monkeypatch.setitem(app.config, "RELEASE_ENABLED", True)
    upload_query = mocker.MagicMock()
    mocker.patch.object(
        Project, "uploads", new_callable=mocker.PropertyMock, return_value=upload_query
    )
    view = view_class()
    handler = mocker.patch.object(view, method.lower(), return_value="allowed")
    with app.test_request_context(method=method):
        login_user(upload_authorization_db.get(User, 1))
        with pytest.raises(NotFound):
            view.dispatch_request(name="test-project", upload_id=123)
    handler.assert_not_called()
    upload_query.filter_by.assert_not_called()


def test_nonlead_member_can_still_access_downloads(app, upload_authorization_db):
    with app.test_request_context():
        login_user(upload_authorization_db.get(User, 1))
        project = UploadDownloadView().project_query("test-project").first()
    assert project.id == 1
