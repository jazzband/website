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
