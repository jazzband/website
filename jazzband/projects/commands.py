import click
from flask.cli import with_appcontext

from ..github import github
from .models import Project


@click.command('projects')
@with_appcontext
def sync_projects():
    "Syncs projects"
    projects_data = github.get_projects()
    Project.sync(projects_data)
