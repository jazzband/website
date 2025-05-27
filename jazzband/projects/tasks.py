from datetime import datetime, timedelta
import json
import logging
import time

from flask import current_app, render_template
from flask_mail import Message
from packaging.version import parse as parse_version
from spinach import Tasks

from ..account import github
from ..config import ONE_MINUTE
from ..db import postgres, redis
from ..email import mail
from ..members.models import EmailAddress, User
from .models import Project, ProjectMembership, ProjectUpload


logger = logging.getLogger(__name__)

tasks = Tasks()


@tasks.task(name="sync_projects", periodicity=timedelta(minutes=30), max_retries=3)
def sync_projects():
    with redis.lock("sync_projects", ttl=ONE_MINUTE * 14):
        projects_data = github.get_projects()
        Project.sync(projects_data)


@tasks.task(name="update_project_by_hook")
def update_project_by_hook(hook_id):
    # first load the hook data again
    hook_data = redis.get(hook_id)
    if not hook_data:
        return
    hook_data = json.loads(hook_data)

    project_name = hook_data["repository"]["name"]
    if project_name in current_app.config["INTERNAL_PROJECTS"]:
        logger.info(f"Skipping project {project_name} since it's internal")
        return

    # then sync the project so it definitely exists
    Project.sync([hook_data["repository"]])
    # get the project again from the database
    project = Project.query.filter(Project.name == project_name).first()

    # use a lock to make sure we don't run this multiple times
    with redis.lock(f"project-update-by-hook-{project_name}", ttl=ONE_MINUTE):
        # if there already was an issue created, just stop here
        if not project.transfer_issue_url:
            # get list of roadies and set them as the default assignees
            roadies = User.query.filter_by(
                is_member=True, is_banned=False, is_roadie=True
            )
            # we'll auto-assign all the roadies, huh huh huh
            assignees = [roadie.login for roadie in roadies]
            # add sender of the hook as well if given
            if "sender" in hook_data:
                assignees.append(hook_data["sender"]["login"])

            # enable issues before creating the transfer issue, with retry logic
            max_retries = 3
            for attempt in range(1, max_retries + 1):
                try:
                    response = github.enable_issues(project_name)
                    if response and response.status_code in (200, 201):
                        break  # Success
                    else:
                        logger.error(
                            f"Attempt {attempt}: Could not enable issues for {project_name}! Status: {getattr(response, 'status_code', None)} | Response: {getattr(response, 'text', None)}"
                        )
                except Exception as exc:
                    logger.exception(
                        f"Attempt {attempt}: Error enabling issues for {project_name}: {exc}"
                    )
                if attempt < max_retries:
                    time.sleep(2)  # Wait 2 seconds before retrying
                else:
                    return  # Abort if all attempts failed
            # create a new issue, finally
            project.create_transfer_issue(assignees, **hook_data)
            logger.info(f"Created new transfer issue for project {project.name}")

        if not project.team_slug:
            # create a team for the project
            project.create_team()
            logger.info(f"Created team for project {project.name}")


@tasks.task(name="send_new_upload_notifications")
def send_new_upload_notifications(project_id=None):
    "Sends project upload notifications if needed"
    unnotified_uploads = ProjectUpload.query.filter_by(notified_at=None)
    if project_id is not None:
        unnotified_uploads = unnotified_uploads.filter_by(project_id=project_id)
    messages = []

    for upload in unnotified_uploads:
        lead_memberships = upload.project.membership.join(
            ProjectMembership.user
        ).filter(
            ProjectMembership.is_lead.is_(True),
            User.is_member.is_(True),
            User.is_banned.is_(False),
        )
        lead_members = [membership.user for membership in lead_memberships]

        recipients = set()

        for lead_member in lead_members + list(User.roadies()):
            primary_email = lead_member.email_addresses.filter(
                EmailAddress.primary.is_(True), EmailAddress.verified.is_(True)
            ).first()

            if not primary_email:
                continue

            recipients.add(primary_email.email)

        message = Message(
            subject=f"Project {upload.project.name} received a new upload",
            recipients=list(recipients),
            body=render_template(
                "projects/mails/new_upload_notification.txt",
                project=upload.project,
                upload=upload,
                lead_members=lead_members,
            ),
        )
        messages.append((upload, message))

    if not messages:
        logger.info("No uploads found without notifications.")
        return

    with mail.connect() as smtp:
        for upload, message in messages:
            try:
                smtp.send(message)
            finally:
                upload.notified_at = datetime.utcnow()
                upload.save(commit=False)
                logger.info(f"Send notification for upload {upload}.")
        postgres.session.commit()


@tasks.task(name="update_upload_ordering", max_retries=10)
def update_upload_ordering(project_id):
    uploads = ProjectUpload.query.filter_by(project_id=project_id).all()

    def version_sorter(upload):
        return parse_version(upload.version)

    for index, upload in enumerate(sorted(uploads, key=version_sorter)):
        upload.ordering = index
        upload.save(commit=False)
    postgres.session.commit()


@tasks.task(
    name="sync_project_members", periodicity=timedelta(minutes=30), max_retries=3
)
def sync_project_members():
    """
    Periodically fetch all team members from GitHub and persist
    project memberships in the database and delete any that aren't
    in GitHub anymore.
    """
    with redis.lock("sync_project_members", ttl=ONE_MINUTE * 14):
        teams = github.get_teams()

        for team in teams:
            project = Project.query.filter(Project.team_slug == team["slug"]).first()
            if project is None:
                continue

            team_members = github.get_members(team["slug"])
            sync_data = [
                {
                    "user_id": team_member["id"],
                    "project_id": project.id,
                }
                for team_member in team_members
            ]

            ProjectMembership.sync(sync_data, key=["user_id", "project_id"])


@tasks.task(name="remove_user_from_team")
def remove_user_from_team(user_id, project_id):
    user = User.query.get(user_id)
    project = Project.query.get(project_id)
    if user and project:
        response = github.leave_team(project.team_slug, user.login)
        if response and response.status_code == 204:
            # this was a success
            return
    logger.error(
        f"Error while removing a user from a project team: {response.json()}",
        extra={
            "user_id": user_id,
            "project_id": project_id,
            "response": response.json() if response else None,
        },
    )


@postgres.event.listens_for(ProjectMembership, "after_delete")
def delete_project_membership(mapper, connection, target):
    """
    When a project membership is deleted we want to remove the user from
    the GitHub team as well.
    """
    tasks.schedule(remove_user_from_team, target.user_id, target.project_id)


@tasks.task(name="add_user_to_team")
def add_user_to_team(user_id, project_id):
    user = User.query.get(user_id)
    project = Project.query.get(project_id)
    if user and project:
        response = github.join_team(project.team_slug, user.login)
        if response and response.status_code == 200:
            # this was a success
            return
    logger.error(
        f"Error while adding a user to a project team: {response.json()}",
        extra={
            "user_id": user_id,
            "project_id": project_id,
            "response": response.json(),
        },
    )


@postgres.event.listens_for(ProjectMembership, "after_insert")
def insert_project_membership(mapper, connection, target):
    """
    When a project membership is added we want to add the user from
    the GitHub team as well.
    """
    tasks.schedule(add_user_to_team, target.user_id, target.project_id)
