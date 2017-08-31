"""
factories.py

@Author: Ogunmokun Olukunle

This module contains application factories.
"""

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_assets import Environment, Bundle
import os
from flask_alembic import Alembic
from flask_restful import Api
from flask_principal import Principal
from flask_mail import Mail
from flask_uploads import UploadSet, IMAGES, ARCHIVES, SCRIPTS, EXECUTABLES, AllExcept, ALL, configure_uploads, \
	patch_request_class
import wtforms_json
from flask_migrate import Migrate
from flask_cache import Cache
import cloudinary
from cloudinary.uploader import upload as cloudinary_upload

cloudinary.config(
    cloud_name='kampusxchange',
    api_key='791467912822196',
    api_secret='R0fI6eyqVWoRlQEs2pSzXeVVeCQ'
)

# # new redis session management
# from flaskext.kvsession import KVSessionExtension
# import redis
# from simplekv.memory.redisstore import RedisStore


# Monkey patch wtforms to support json data
wtforms_json.init()


def initialize_api(app, api):
    """ Register all resources for the API """
    api.init_app(app=app)  # Initialize api first
    _resources = getattr(app, "api_registry", None)
    if _resources and isinstance(_resources, (list, tuple,)):
        for cls, args, kwargs in _resources:
            api.add_resource(cls, *args, **kwargs)


def initialize_blueprints(app, *blueprints):
    """
    Registers a set of blueprints to an application
    """
    for blueprint in blueprints:
        app.register_blueprint(blueprint)


# def make_celery(app):
# 	""" Enables celery to run within the flask application context """

# 	celery = Celery(app.import_name, backend=app.config['CELERY_BROKER_URL'], broker=app.config['CELERY_BROKER_URL'])
# 	celery.conf.update(app.config)
# 	TaskBase = celery.Task

# 	class ContextTask(TaskBase):
# 		abstract = True
# 		def __call__(self, *args, **kwargs):
# 			with app.app_context():
# 				return TaskBase.__call__(self, *args, **kwargs)

# 	celery.Task = ContextTask
# 	return celery


def create_app(app_name, config_obj, with_api=True):
    """ Generates and configures the main shop application. All additional """
    # Launching application
    app = Flask(app_name)  # So the engine would recognize the root package

    # Load Configuration
    app.config.from_object(config_obj)

    # Initializing Database
    db = SQLAlchemy(app)
    app.db = db

    # migrate = Migrate(app, db)
    alembic = Alembic()
    alembic.init_app(app)
    app.alembic = alembic

    # Loading assets
    assets = Environment(app)
    assets.from_yaml('assets.yaml')
    app.assets = assets

    # Initialize Mail
    app.mail = Mail(app)

    # Initializing login manager
    login_manager = LoginManager()
    login_manager.login_view = app.config.get('LOGIN_VIEW', '.login')
    # login_manager.login_message = 'You need to be logged in to access this page'
    login_manager.session_protection = 'strong'
    login_manager.setup_app(app)
    app.login_manager = login_manager

    # Initializing principal manager
    app.principal = Principal(app)

    # Initializing bcrypt password encryption
    bcrypt = Bcrypt(app)
    app.bcrypt = bcrypt

    app.cloudinary = cloudinary
    app.cloudinary_upload = cloudinary_upload

    photos = UploadSet('photos', IMAGES)
    archives = UploadSet('archives', ARCHIVES)

    configure_uploads(app, (photos, archives))

    patch_request_class(app, 16 * 1024 * 1024)  # Patches to 16MB file uploads max.

    app.photos = photos
    app.archives = archives

    # Redis store for session management
    # The process running Flask needs write access to this directory:
    # store = RedisStore(redis.StrictRedis())

    # # this will replace the app'cs session handling
    # KVSessionExtension(store, app)

    # # configure sentry
    # if not app.config.get("DEBUG", False):
    # 	sentry = Sentry(app)

    # 	app.sentry = sentry

    # Integrate Elasticsearch

    # es_config = app.config.get("ES_CONFIG", [])

    # app.es = Elasticsearch(es_config)

    # Caching
    app.cache = Cache(app)

    # Initializing the restful API
    if with_api:
        api = Api(app, prefix='/v1')
        app.api = api

    # Initialize Logging
    if not app.debug:
        import logging
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler("/var/log/kx/%s.log" % app.config.get("LOGFILE_NAME", app_name),
                                           maxBytes=500 * 1024)
        file_handler.setLevel(logging.INFO)
        from logging import Formatter
        file_handler.setFormatter(Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))
        app.logger.addHandler(file_handler)

        # Implement Sentry logging here
        sentry = Sentry(app)
        app.sentry = sentry

    # include an api_registry to the application
    app.api_registry = []  # a simple list holding the values to be registered

    return app
