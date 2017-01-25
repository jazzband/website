from ..github import github
from .models import Project


def sync_projects():
    "Syncs projects"
    projects_data = github.get_projects()
    Project.sync(projects_data)
