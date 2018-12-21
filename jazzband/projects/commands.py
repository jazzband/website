import click
import click_log
import logging
from flask.cli import with_appcontext

from ..github import github
from . import jobs
from .models import Project


logger = logging.getLogger(__name__)
click_log.basic_config(logger)


@click.command('projects')
@with_appcontext
def sync_projects():
    "Syncs projects"
    projects_data = github.get_projects()
    Project.sync(projects_data)


@click.command('new_upload_notifications')
@click_log.simple_verbosity_option(logger)
@with_appcontext
def send_new_upload_notifications(project_id=None):
    return jobs.send_new_upload_notifications(project_id)
