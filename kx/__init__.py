# Imports
from flask import current_app as app
from flask.ext import restful
from sqlalchemy import exc
from sqlalchemy import event
from sqlalchemy.pool import Pool
import os

#Retrieve the current application and expand it's properties

#Logger
logger = app.logger

#Bcrypt
bcrypt = app.bcrypt

# Database
db = app.db

# API
api = app.api

# Login Manager
login_manager = app.login_manager

# Authorization Principal
principal = app.principal

# Mail
mail = app.mail

# CSS/JS Assets
assets = app.assets

# Uploaders
photos = app.photos
archives = app.archives

# Celery
# celery = app.celery

# Elasticsearch
# es = app.es

#Redis
# redis = app.redis

cache = app.cache
cloudinary = app.cloudinary
cloudinary_upload = app.cloudinary_upload

# Connection pool disconnect handler. Brought about as a result of MYSQL!!!

@event.listens_for(Pool, "checkout")
def ping_connection(dbapi_connection, connection_record, connection_proxy):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("SELECT 1")
    except:
        # optional - dispose the whole pool
        # instead of invalidating one at a time
        # connection_proxy._pool.dispose()

        # raise DisconnectionError - pool will try
        # connecting again up to three times before raising.
        raise exc.DisconnectionError()
    cursor.close()


def register_api(cls, *urls, **kwargs):
	""" A simple pass through class to add entities to the api registry """
	kwargs["endpoint"] = getattr(cls, 'resource_name', kwargs.get("endpoint", None))
	app.api_registry.append((cls, urls, kwargs))
