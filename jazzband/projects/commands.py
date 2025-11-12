import logging

import click
import click_log
from flask.cli import with_appcontext

from ..account import github
from . import tasks
from .models import Project


logger = logging.getLogger(__name__)
click_log.basic_config(logger)


@click.command("projects")
@click_log.simple_verbosity_option(logger)
@with_appcontext
def sync_projects():
    "Syncs projects"
    tasks.sync_projects()


@click.command("project_members")
@click_log.simple_verbosity_option(logger)
@with_appcontext
def sync_project_members():
    "Syncs project members"
    tasks.sync_project_members()


@click.command("new_upload_notifications")
@click.option("--project_id", "-p", default=None)
@click_log.simple_verbosity_option(logger)
@with_appcontext
def send_new_upload_notifications(project_id):
    tasks.send_new_upload_notifications(project_id)


@click.command("project_team")
@click.argument("name")
@click_log.simple_verbosity_option(logger)
@with_appcontext
def sync_project_team(name):
    "Syncs (create/populate) project team"
    project = Project.query.filter(Project.name == name).first()
    team_response = github.get_project_team(project.name)

    if team_response.status_code == 404:
        logger.info(f"Project team {name} doesn't exist yet. Creating..")
        team_response = project.create_team()

    elif team_response.status_code == 200:
        logger.info(f"Project team {name} already exists.")

    team_response.raise_for_status()
    if team_response:
        team_data = team_response.json()
        for lead in project.lead_members.all():
            logging.info(f"Adding @{lead.login} to project team {name}")
            member_response = github.join_team(team_data["slug"], lead.login)
            member_response.raise_for_status()
    else:
        logging.error(
            f"Something went wrong while syncing project team for project {name}"
        )


@click.command("project_leads_team")
@click.argument("name")
@click_log.simple_verbosity_option(logger)
@with_appcontext
def setup_project_leads_team(name):
    """Setup leads team for a project (creates team, adds leads, grants maintain permissions)"""
    project = Project.query.filter(Project.name == name).first()
    if not project:
        logger.error(f"Project {name} not found")
        print(f"❌ Project {name} not found")
        return

    try:
        logger.info(f"Setting up leads team for project {name}")
        print(f"Setting up leads team for project {name}...")
        tasks.setup_project_leads_team(project.id)
        print(f"✅ Successfully set up leads team for {name}")
    except Exception as exc:
        logger.error(f"Failed to setup leads team for {name}: {exc}")
        print(f"❌ Failed to setup leads team for {name}: {exc}")
        raise


@click.command("add_repo_to_members_team")
@click.argument("name")
@click.option(
    "--permission",
    "-p",
    default="push",
    help="Permission level (pull, push, maintain, admin)",
)
@click_log.simple_verbosity_option(logger)
@with_appcontext
def add_repo_to_members_team(name, permission):
    """Add a repository to the members team with specified permissions"""
    try:
        logger.info(f"Adding repo {name} to members team with {permission} permission")
        print(f"Adding repo {name} to members team with {permission} permission...")
        tasks.add_repo_to_members_team(name, permission)
        print(f"✅ Successfully added {name} to members team")
    except Exception as exc:
        logger.error(f"Failed to add {name} to members team: {exc}")
        print(f"❌ Failed to add {name} to members team: {exc}")
        raise


@click.command("update_all_projects_members_team")
@click.option(
    "--permission",
    "-p",
    default="push",
    help="Permission level (pull, push, maintain, admin)",
)
@click_log.simple_verbosity_option(logger)
@with_appcontext
def update_all_projects_members_team(permission):
    """Update all active projects to be assigned to members team with write permissions"""
    try:
        logger.info(
            f"Updating all projects to members team with {permission} permission"
        )
        print(
            f"Updating all active projects to members team with {permission} permission..."
        )
        tasks.update_all_projects_members_team(permission)
        print("✅ Successfully updated all projects")
    except Exception as exc:
        logger.error(f"Failed to update all projects: {exc}")
        print(f"❌ Failed to update all projects: {exc}")
        raise
