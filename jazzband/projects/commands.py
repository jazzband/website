import logging

import click
import click_log
from flask.cli import with_appcontext

from . import tasks

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
    "Syncs projects"
    tasks.sync_project_members()


@click.command("new_upload_notifications")
@click_log.simple_verbosity_option(logger)
@with_appcontext
def send_new_upload_notifications(project_id=None):
    tasks.send_new_upload_notifications(project_id)
