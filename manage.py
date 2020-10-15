#!/usr/bin/python
# -*- coding: utf-8 -*-

from app import create_app, db
from app.main.scheduler import init_scheduler
from flask_script import Manager, Shell
from flask_migrate import MigrateCommand, Migrate
from flask_cors import CORS

app = create_app('default')
CORS(app, resources=r'/*')

init_scheduler(app)

manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db)


manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)

if __name__ == "__main__":
    manager.run()