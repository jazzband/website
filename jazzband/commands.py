from flask.ext.script import Command

from .github import github
from .models import db, User, Project


class SyncProjects(Command):
    "Syncs Jazzband projects on GitHub with database"

    def run(self):
        projects_data = github.get_projects()
        Project.sync(projects_data)


class SyncMembers(Command):
    "Syncs Jazzband members on GitHub with database"

    def run(self):
        members_data = github.get_members()
        User.sync(members_data)

        stored_ids = set(user.id for user in User.query.all())
        fetched_ids = set(m['id'] for m in members_data)
        stale_ids = stored_ids - fetched_ids
        if stale_ids:
            User.query.filter(
                User.id.in_(stale_ids)
            ).update({'is_member': False}, 'fetch')
            db.session.commit()
