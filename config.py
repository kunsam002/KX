# Configuration module

import os


class Config(object):
    """
	Base configuration class. Subclasses should include configurations for
	testing, development and production environments

	"""

    DEBUG = True
    SECRET_KEY = '\x91c~\xc0-\xe3\'f\xe19PE\x93\xe8\x91`uu"\xd0\xb6\x01/\x0c\xed\\\xbd]H\x99k\xf8'
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_POOL_RECYCLE = 1 * 60 * 60

    ADMIN_EMAILS = ["kunsam002@gmail.com"]

    EMAIL_DEV_ONLY = True

    # File uploads
    UPLOADS_DEFAULT_DEST = os.path.join(os.path.dirname(os.path.abspath(__name__)), "uploads")

    FLASK_ASSETS_USE_S3 = False
    USE_S3 = False
    USE_S3_DEBUG = DEBUG
    ASSETS_DEBUG = True
    S3_USE_HTTPS = False

    LOGFILE_NAME = "kx"

    ADMIN_USERNAME = "kx"
    ADMIN_PASSWORD = "kx"
    ADMIN_EMAIL = "admin@kx.com"
    ADMIN_FULL_NAME = "kx"

    # Facebook, Twitter and Google Plus handles
    SOCIAL_LINKS = {"facebook": "", "twitter": "", "google": "",
                    "instagram": "", "pinterest": ""}

    # ReCaptcha Keys
    RECAPTCHA_PUB_KEY = "6LeC-OgSAAAAAOjhuihbl6ks-NxZ9jzcv7X4kG9M"
    RECAPTCHA_PRIV_KEY = "6LeC-OgSAAAAANbUdjXj_YTCHbocDQ48-bRRFYTr"




class SiteDevConfig(Config):
    """ Configuration class for site development environment """

    DEBUG = True

    SQLALCHEMY_DATABASE_URI = 'mysql+mysqldb://kx:kx@localhost/kx'

    DATABASE = SQLALCHEMY_DATABASE_URI
    SETUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__name__)), 'setup')
    MAX_RETRY_COUNT = 3


    LOGIN_VIEW = '.login'
