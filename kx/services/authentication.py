__author__ = 'kunsam002'
"""
authentication.py
@Author: Ogunmokun Olukunle

This module is responsible for authenticating a user and handling permissions
for users in the system.

"""

from kx import login_manager, app, logger, db
from kx.models import User
from kx.signals import *
from kx.services import ServiceFactory
from sqlalchemy import or_, and_
from flask.ext.login import current_user
from flask.ext.principal import identity_loaded, UserNeed, RoleNeed
import hashlib
from kx import bcrypt
from flask import url_for

# ConfirmationTokenService = ServiceFactory.create_service(ConfirmationToken, db)

@login_manager.user_loader
def load_user(user_id):
    """
    Retrieves a user using the id stored in the session.

    :param userid: The user id (fetched from the session)

    :returns: the logged in user or None

    """
    return User.query.get(user_id)


# @login_manager.token_loader
# def load_user_token(token):
# 	"""
# 	Retrieves a user using the auth_token stored in the session

# 	:param token: The token used to identify the user (fetched from the session)

# 	:returns: the logged in user or None
# 	"""

# 	try:
# 		data = token.split(":")
# 		if len(data) == 2:
# 			user = User.query.get(data[0])
# 			if user and hashlib.md5(user.password).hexdigest() == data[1]:
# 				return user
# 	except:
# 		pass

# 	return None


@identity_loaded.connect
def on_identity_loaded(sender, identity):
	"""
	Loads a current user's roles into the identity context
	"""

	identity.user = current_user

	# Add the UserNeed to the identity
	if hasattr(identity.user, "id"):
		identity.provides.add(UserNeed(identity.user.id))

	# Assuming the current user has a list of roles, update the
	# identity with the roles that the user provides
	if hasattr(identity.user, "roles"):
		for role in identity.user.roles:
			identity.provides.add(RoleNeed(role.name))



def authenticate_user(username, password, **kwargs):
	"""
	"""
	user = User.query.filter(and_(User.is_super_admin==False)).filter(or_(User.username==username, User.email==username)).first()


	logger.info(password)
	logger.info(user)
	logger.info(user.password)
	logger.info(bcrypt.generate_password_hash(password))
	if user and user.check_password(password):
		user.update_last_login()
		# search.index(user)
		return user
	else:
		return None


def authenticate_forgot_password(username, **kwargs):
	"""
	"""
	user = User.query.filter(and_(User.is_super_admin==False, User.is_staff==False)).filter(or_(User.username==username, User.email==username)).first()
	if user:
		# search.index(user)
		return user
	else:
		return None



def authenticate_admin(username, password, **kwargs):
	"""
	Fetch a user based on the given username and password.

	:param username: the username (or email address) of the user
	:param password: password credential
	:param kwargs: additional parameters required

	:returns: a user object or None
	"""
	user = User.query.filter(and_(User.is_super_admin==True, User.is_staff==True)).filter(or_(User.username==username, User.email==username)).first()
	if user and user.check_password(password):
		# search.index(user)
		return user
	else:
		return None



def check_basic_auth(username, auth_token, **kwargs):
	"""
	Fetch a user based on the given username and token key given.
	This is used along with HTTP Basic Authentication

	:param username: the username (or email address) of the user
	:param auth_token: authentication token generated for the user

	:returns: a user object or None

	"""
	logger.info("checking basic auth")
	user = User.query.filter(or_(User.matric==username, User.email==username, User.phone==username)).first()
	if user and auth_token == user.get_auth_token():
		# search.index(user)
		return user
	else:
		return None


def require_basic_auth(realm="MTN-DML API"):
	""" Sends a 401 Authorization required response that enables basic auth """

	message = "Could not authorize your request. Provide the proper login credentials to continue."

	headers = {"WWW-Authenticate": "Basic realm='%s'" % realm}
	status = 401

	return message, status, headers # body, status and headers


def check_admin_auth(username, auth_token, **kwargs):
	"""
	Fetch a user based on the given username and token key given.
	This is used along with HTTP Basic Authentication

	:param username: the username (or email address) of the user
	:param auth_token: authentication token generated for the user

	:returns: a user object or None

	"""
	user = User.query.filter(or_(User.username==username, User.email==username)).first()
	if user and auth_token == user.get_auth_token():
		# search.index(user)
		return user
	else:
		return None
