# Imports
from flask import current_app as app
from sqlalchemy import exc
from sqlalchemy import event
from sqlalchemy.pool import Pool
import os
from PIL import Image as PImage

# Retrieve the current application and expand it's properties

# Logger
logger = app.logger

# Bcrypt
bcrypt = app.bcrypt

# Database
db = app.db

alembic = app.alembic

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

moment = app.moment

# Celery
# celery = app.celery

# Elasticsearch
# es = app.es

# Redis
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


def check_image_size(src, dimensions=(200, 200), square=True):
    """
    Check's image dimensions. If square is true,
    check that the image is a square,
    else check that it matches the dimensions

    """

    img = PImage.open(src)
    width, height = img.size
    d_width, d_height = dimensions

    return True


def handle_uploaded_photos(files, dimensions=(400, 400), square=True):
    """ Handles file uploads """

    uploaded_files = []
    errors = []

    for _f in files:
        try:
            filename = photos.save(_f)
            path = photos.path(filename)
            if check_image_size(path, dimensions, square):
                data = {"name": filename, "path": path}
                uploaded_files.append(data)
            else:
                errors.append("%s is not the right dimension" % filename)
        except Exception, e:
            logger.info(e)
            errors.append("Uploading %s is not allowed" % _f.filename)

    return uploaded_files, errors


def register_api(cls, *urls, **kwargs):
    """ A simple pass through class to add entities to the api registry """
    kwargs["endpoint"] = getattr(cls, 'resource_name', kwargs.get("endpoint", None))
    app.api_registry.append((cls, urls, kwargs))


@app.teardown_request
def shutdown_session(exception=None):
    print "------------- tearing down context now ---------"
    if exception:
        db.session.rollback()
        db.session.close()
        db.session.remove()
    db.session.close()
    db.session.remove()


@app.teardown_appcontext
def teardown_db(exception=None):
    print "------------- tearing down app context now ---------"
    db.session.commit()
    db.session.close()
    db.session.remove()
