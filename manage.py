#!/usr/bin/env python
from flask.ext.assets import ManageAssets
from flask.ext.script import Manager

from jazzband import app, assets

manager = Manager(app)

manager.add_command("assets", ManageAssets(assets))


if __name__ == "__main__":
    manager.run()
