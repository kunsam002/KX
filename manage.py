#! /usr/bin/env python
import flask
from flask.ext.script import Manager
import os
from flask.ext.assets import ManageAssets
from factories import create_app, initialize_api, initialize_blueprints
from flask.ext.migrate import MigrateCommand
from model_migrations import *
from xlrd import open_workbook

app = create_app('kx', 'config.SiteDevConfig')

logger = app.logger

# Initializing script manager
manager = Manager(app)
# add assets command to it
manager.add_command("assets", ManageAssets(app.assets))

manager.add_command('db', MigrateCommand)

SETUP_DIR = app.config.get("SETUP_DIR")


@manager.command
def runserver():
    """ Start the server"""
    # with app2.app_context():
    from kx.views.public import www
    from kx import api, principal
    from kx.resources import resource

    # Initialize the app blueprints
    initialize_blueprints(app, www)
    initialize_api(app, api)

    port = int(os.environ.get('PORT', 5500))
    app.run(host='0.0.0.0', port=port)


@manager.command
def runadmin():
    """ Start the backend server server"""
    # with app2.app_context():
    from kx.views.admin import control
    # Initialize the app blueprints
    initialize_blueprints(app, control)

    port = int(os.environ.get('PORT', 5550))
    app.run(host='0.0.0.0', port=port)


@manager.command
def syncdb(refresh=False):
    """
    Synchronizes (or initializes) the database
    :param refresh: drop and recreate the database
    """
    # Apparently, we need to import the models file before this can work right.. smh @flask-sqlalchemy
    from kx import db, models
    if refresh:
        logger.info("Dropping database tables")
        db.drop_all()
    logger.info("Creating database tables")
    db.create_all()
    db.session.flush()


@manager.command
def refresh_db():
    syncdb(refresh=True)

@manager.command
def install_assets():
    """ Installs all required assets to begin with """
    from startup import start
    start()


@manager.command
def setup_app():
    syncdb()
    install_assets()



if __name__ == "__main__":
    manager.run()
