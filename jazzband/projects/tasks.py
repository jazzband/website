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

        # Add the repository to the members team with write permissions
        members_team_slug = github.members_team_slug
        if members_team_slug:
            logger.info(
                f"Adding repo {project.name} to members team {members_team_slug} with push permission"
            )
            repo_response = github.add_repo_to_team(
                members_team_slug, project.name, "push"
            )
            if repo_response and repo_response.status_code == 204:
                logger.info(f"Successfully added repo {project.name} to members team")
            else:
                logger.error(
                    f"Failed to add repo {project.name} to members team",
                    extra={
                        "project_name": project.name,
                        "status_code": repo_response.status_code
                        if repo_response
                        else None,
                        "response": repo_response.json() if repo_response else None,
                    },
                )


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
def remove_user_from_team(user_id, project_id, is_lead=False):
    user = User.query.get(user_id)
    project = Project.query.get(project_id)
    if user and project:
        # First remove from leads team if they were a lead
        if is_lead and project.leads_team_slug:
            logger.info(
                f"Removing @{user.login} from leads team {project.leads_team_slug}"
            )
            leads_response = github.leave_team(project.leads_team_slug, user.login)
            if leads_response and leads_response.status_code == 204:
                logger.info(f"Successfully removed @{user.login} from leads team")
            else:
                logger.error(
                    f"Failed to remove @{user.login} from leads team {project.leads_team_slug}",
                    extra={
                        "user_id": user_id,
                        "project_id": project_id,
                        "status_code": leads_response.status_code
                        if leads_response
                        else None,
                        "response": leads_response.json() if leads_response else None,
                    },
                )

        # Now remove from the main project team
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
    tasks.schedule(
        remove_user_from_team, target.user_id, target.project_id, target.is_lead
    )


@tasks.task(name="add_user_to_team")
def add_user_to_team(user_id, project_id, is_lead=False):
    user = User.query.get(user_id)
    project = Project.query.get(project_id)
    if user and project:
        response = github.join_team(project.team_slug, user.login)
        if response and response.status_code == 200:
            # this was a success, now check if we need to add to leads team
            if is_lead and project.leads_team_slug:
                logger.info(
                    f"Adding @{user.login} to leads team {project.leads_team_slug}"
                )
                leads_response = github.join_team(project.leads_team_slug, user.login)
                if leads_response and leads_response.status_code == 200:
                    logger.info(f"Successfully added @{user.login} to leads team")
                else:
                    logger.error(
                        f"Failed to add @{user.login} to leads team {project.leads_team_slug}",
                        extra={
                            "user_id": user_id,
                            "project_id": project_id,
                            "status_code": leads_response.status_code
                            if leads_response
                            else None,
                            "response": leads_response.json()
                            if leads_response
                            else None,
                        },
                    )
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
    tasks.schedule(add_user_to_team, target.user_id, target.project_id, target.is_lead)


@postgres.event.listens_for(ProjectMembership, "after_update")
def update_project_membership(mapper, connection, target):
    """
    When a project membership is updated, check if is_lead status changed
    and add/remove from leads team accordingly.
    """
    # Get the previous state from the history
    history = postgres.inspect(target).attrs.is_lead.history
    if history.has_changes():
        old_value = history.deleted[0] if history.deleted else False
        new_value = target.is_lead

        # If promoted to lead, add to leads team
        if not old_value and new_value:
            tasks.schedule(add_user_to_leads_team, target.user_id, target.project_id)
        # If demoted from lead, remove from leads team
        elif old_value and not new_value:
            tasks.schedule(
                remove_user_from_leads_team, target.user_id, target.project_id
            )


@tasks.task(name="add_user_to_leads_team")
def add_user_to_leads_team(user_id, project_id):
    """Add a user to the project's leads team on GitHub."""
    user = User.query.get(user_id)
    project = Project.query.get(project_id)

    if not user or not project:
        logger.error(f"User {user_id} or project {project_id} not found")
        return

    if not project.leads_team_slug:
        logger.warning(
            f"Project {project.name} has no leads team, cannot add @{user.login} to leads team"
        )
        return

    logger.info(f"Adding @{user.login} to leads team {project.leads_team_slug}")
    response = github.join_team(project.leads_team_slug, user.login)

    if response and response.status_code == 200:
        logger.info(f"Successfully added @{user.login} to leads team")
    else:
        logger.error(
            f"Failed to add @{user.login} to leads team {project.leads_team_slug}",
            extra={
                "user_id": user_id,
                "project_id": project_id,
                "status_code": response.status_code if response else None,
                "response": response.json() if response else None,
            },
        )


@tasks.task(name="remove_user_from_leads_team")
def remove_user_from_leads_team(user_id, project_id):
    """Remove a user from the project's leads team on GitHub."""
    user = User.query.get(user_id)
    project = Project.query.get(project_id)

    if not user or not project:
        logger.error(f"User {user_id} or project {project_id} not found")
        return

    if not project.leads_team_slug:
        logger.info(
            f"Project {project.name} has no leads team, nothing to remove for @{user.login}"
        )
        return

    logger.info(f"Removing @{user.login} from leads team {project.leads_team_slug}")
    response = github.leave_team(project.leads_team_slug, user.login)

    if response and response.status_code == 204:
        logger.info(f"Successfully removed @{user.login} from leads team")
    else:
        logger.error(
            f"Failed to remove @{user.login} from leads team {project.leads_team_slug}",
            extra={
                "user_id": user_id,
                "project_id": project_id,
                "status_code": response.status_code if response else None,
                "response": response.json() if response else None,
            },
        )


@tasks.task(name="setup_project_leads_team")
def setup_project_leads_team(project_id, dry_run=False):
    """
    Create a leads sub-team for a project, add all lead members to it,
    and grant them maintain permissions to the repository.

    Args:
        project_id: The ID of the project
        dry_run: If True, log what would be done without making changes
    """
    log_prefix = "[DRY RUN] " if dry_run else ""

    project = Project.query.get(project_id)
    if not project:
        logger.error(f"{log_prefix}Project with id {project_id} not found")
        return

    if not project.team_slug:
        logger.error(
            f"{log_prefix}Project {project.name} has no team_slug, cannot create leads team"
        )
        return

    # Check if project has any leads
    lead_members = project.lead_members.all()
    if not lead_members:
        logger.info(
            f"{log_prefix}Project {project.name} has no lead members, skipping leads team setup"
        )
        return

    # Check if leads team already exists in database
    if project.leads_team_slug:
        logger.info(
            f"{log_prefix}Project {project.name} already has a leads team in DB: {project.leads_team_slug}"
        )
        leads_team_slug = project.leads_team_slug

        if not dry_run:
            # Verify it still exists on GitHub
            team_response = github.get_project_team(leads_team_slug)
            if team_response.status_code != 200:
                logger.warning(
                    f"Leads team {leads_team_slug} in DB but not found on GitHub, will recreate"
                )
                project.leads_team_slug = None
                project.save()
                leads_team_slug = None
    else:
        leads_team_slug = None

    # Check if leads team exists on GitHub but not in DB (manually created)
    if not leads_team_slug:
        potential_slug = f"{project.name}-leads"

        if dry_run:
            logger.info(
                f"{log_prefix}Would check for existing team {potential_slug} and create if needed"
            )
            leads_team_slug = potential_slug  # Use potential slug for dry-run
        else:
            test_response = github.get_project_team(potential_slug)
            if test_response.status_code == 200:
                logger.info(
                    f"Found manually created leads team {potential_slug}, updating DB"
                )
                project.leads_team_slug = potential_slug
                project.save()
                leads_team_slug = potential_slug
            else:
                # Create the leads team
                logger.info(f"Creating leads team for project {project.name}")
                leads_response = project.create_leads_team()

                if not leads_response or leads_response.status_code != 201:
                    logger.error(
                        f"Failed to create leads team for project {project.name}",
                        extra={
                            "project_id": project_id,
                            "status_code": leads_response.status_code
                            if leads_response
                            else None,
                            "response": leads_response.json()
                            if leads_response
                            else None,
                        },
                    )
                    return

                leads_team_slug = project.leads_team_slug
                logger.info(
                    f"Created leads team {leads_team_slug} for project {project.name}"
                )

    # Add all lead members to the leads team
    for lead in lead_members:
        logger.info(f"{log_prefix}Adding @{lead.login} to leads team {leads_team_slug}")

        if not dry_run:
            response = github.join_team(leads_team_slug, lead.login)
            if response and response.status_code == 200:
                logger.info(f"Successfully added @{lead.login} to {leads_team_slug}")
            else:
                logger.error(
                    f"Failed to add @{lead.login} to {leads_team_slug}",
                    extra={
                        "user_login": lead.login,
                        "team_slug": leads_team_slug,
                        "status_code": response.status_code if response else None,
                        "response": response.json() if response else None,
                    },
                )

    # Grant the leads team maintain permissions to the repository
    logger.info(
        f"{log_prefix}Granting maintain permissions to {leads_team_slug} for repo {project.name}"
    )

    if not dry_run:
        repo_response = github.add_repo_to_team(
            leads_team_slug, project.name, "maintain"
        )
        if repo_response and repo_response.status_code == 204:
            logger.info(
                f"Successfully granted maintain permissions to {leads_team_slug} for {project.name}"
            )
        else:
            logger.error(
                f"Failed to grant maintain permissions to {leads_team_slug} for {project.name}",
                extra={
                    "project_name": project.name,
                    "team_slug": leads_team_slug,
                    "status_code": repo_response.status_code if repo_response else None,
                    "response": repo_response.json() if repo_response else None,
                },
            )


@tasks.task(name="add_repo_to_members_team")
def add_repo_to_members_team(project_name, permission="push", dry_run=False):
    """
    Add a repository to the members team with the specified permissions.

    Args:
        project_name: The name of the project/repository
        permission: The permission level (pull, push, maintain, admin). Default is 'push' (write).
        dry_run: If True, log what would be done without making changes
    """
    log_prefix = "[DRY RUN] " if dry_run else ""
    members_team_slug = github.members_team_slug
    if not members_team_slug:
        logger.error(f"{log_prefix}Members team slug not configured")
        return

    logger.info(
        f"{log_prefix}Adding repo {project_name} to members team {members_team_slug} with {permission} permission"
    )

    if not dry_run:
        response = github.add_repo_to_team(members_team_slug, project_name, permission)

        if response and response.status_code == 204:
            logger.info(
                f"Successfully added repo {project_name} to members team with {permission} permission"
            )
        else:
            logger.error(
                f"Failed to add repo {project_name} to members team",
                extra={
                    "project_name": project_name,
                    "permission": permission,
                    "status_code": response.status_code if response else None,
                    "response": response.json() if response else None,
                },
            )


@tasks.task(name="update_all_projects_members_team")
def update_all_projects_members_team(permission="push", dry_run=False):
    """
    Update all active projects to be assigned to the members team with write permissions.

    Args:
        permission: The permission level (pull, push, maintain, admin). Default is 'push' (write).
        dry_run: If True, log what would be done without making changes
    """
    log_prefix = "[DRY RUN] " if dry_run else ""
    members_team_slug = github.members_team_slug
    if not members_team_slug:
        logger.error(f"{log_prefix}Members team slug not configured")
        return

    projects = Project.query.filter_by(is_active=True).all()
    logger.info(
        f"{log_prefix}Updating {len(projects)} active projects to be assigned to members team with {permission} permission"
    )

    # First, get all repos already in the members team to avoid unnecessary API calls
    logger.info(f"{log_prefix}Fetching existing repos in members team...")
    existing_repos = {}
    
    if not dry_run:
        try:
            # get_team_repos uses all_pages=True, so it returns a list directly
            team_repos = github.get_team_repos(members_team_slug)
            if team_repos:
                for repo in team_repos:
                    # Store repo name and current permission
                    existing_repos[repo["name"]] = repo.get("permissions", {})
                logger.info(f"Found {len(existing_repos)} repos already in members team")
            else:
                logger.warning("Could not fetch existing team repos, will update all")
        except Exception as exc:
            logger.warning(f"Error fetching existing team repos: {exc}, will update all")

    success_count = 0
    error_count = 0
    skip_count = 0

    for project in projects:
        # Check if repo already has correct permissions
        if project.name in existing_repos and not dry_run:
            current_perms = existing_repos[project.name]
            # Check if the desired permission is already set
            has_permission = current_perms.get(permission, False)
            if has_permission:
                logger.info(f"SKIP: {project.name} already has {permission} permission")
                skip_count += 1
                continue

        logger.info(f"{log_prefix}Processing project {project.name} (id: {project.id})")

        if not dry_run:
            response = github.add_repo_to_team(
                members_team_slug, project.name, permission
            )

            if response and response.status_code == 204:
                logger.info(
                    f"Successfully updated {project.name} with {permission} permission"
                )
                success_count += 1
            else:
                logger.error(
                    f"Failed to update {project.name}",
                    extra={
                        "project_id": project.id,
                        "project_name": project.name,
                        "permission": permission,
                        "status_code": response.status_code if response else None,
                        "response": response.json() if response else None,
                    },
                )
                error_count += 1
        else:
            # In dry-run, show if it would skip or update
            if project.name in existing_repos:
                logger.info(f"{log_prefix}Would verify/update {project.name}")
            else:
                logger.info(f"{log_prefix}Would add {project.name} to members team")
            success_count += 1

    logger.info(
        f"Finished updating projects. Success: {success_count}, Skipped: {skip_count}, Errors: {error_count}"
    )
