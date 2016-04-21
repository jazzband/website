#!/usr/bin/env python
from flask.ext.assets import ManageAssets
from flask.ext.script import Manager
from flask_migrate import MigrateCommand

from jazzband.app import create_app
from jazzband.assets import assets
from jazzband.commands import SyncMembers, SyncProjects


app = create_app('jazzband.config')

manager = Manager(app)
manager.add_command('assets', ManageAssets(assets))
manager.add_command('db', MigrateCommand)
manager.add_command('sync_members', SyncMembers())
manager.add_command('sync_projects', SyncProjects())


if __name__ == "__main__":
    manager.run()
