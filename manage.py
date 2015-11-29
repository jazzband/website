#!/usr/bin/env python
from flask.ext.assets import ManageAssets
from flask.ext.script import Manager

from jazzband.app import create_app
from jazzband.assets import assets


app = create_app('jazzband.settings')

manager = Manager(app)

manager.add_command("assets", ManageAssets(assets))


if __name__ == "__main__":
    manager.run()
