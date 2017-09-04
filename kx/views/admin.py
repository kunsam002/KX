"""
admin.py

@Author: Ogunmokun, Olukunle

The admin views required to sign up and get started
"""

from flask import Blueprint, render_template, abort, redirect, \
    flash, url_for, request, session, g, make_response, current_app, jsonify
from flask_login import logout_user, login_required, login_user, current_user
from kx import db, logger, app, handle_uploaded_photos
from kx.forms import *
from kx.services import *
from kx.services import users, site_services, operations
from kx.services.authentication import authenticate_admin
from datetime import date, datetime, timedelta
from kx.models import *
from sqlalchemy import asc, desc, or_, and_, func
from kx.forms import *
from kx.core import utils, templating
from kx.core.utils import build_page_url
from kx.signals import *
import time
import json
import urllib
from flask_principal import Principal, Identity, AnonymousIdentity, identity_changed, PermissionDenied
import base64
import requests
import xmltodict
import os
import sys
import random
from pprint import pprint
import cgi
control = Blueprint('admin', __name__, template_folder='../templates', static_folder='../static')


@app.errorhandler(404)
def page_not_found(e):
    title = "404- Page Not Found"
    error_number = "404"
    error_title = "Page not found!"
    error_info = "The requested page cannot be found or does not exist. Please contact the Administrator."

    return render_template('public/error.html', **locals()), 404


@app.errorhandler(500)
def internal_server_error(e):
    title = "500- Internal Server Error"
    error_number = "500"
    error_title = "Server Error!"
    error_info = "There has been an Internal server Error. Please try again later or Contact the Administrator."

    return render_template('public/error.html', **locals()), 500


@app.errorhandler(PermissionDenied)
def page_access_denied(e):
    return render_template('admin/access_denied.html'), 403


# def _check_notification(code):
# 	""" checks notifications for display in the template. It returns either a number or an empty string """
# 	notifiers = {
# 	"messages": check_unread_messages,
# 	"complaints": check_unread_complaints
# 	}

# 	func = notifiers.get(code, None)

# 	if func:
# 		return func()
# 	else:
# 		return ""


# def check_unread_messages():
# 	""" This returns the number of unread messages """
# 	unread = AdminMessage.query.filter(Message.is_read==False).count()

# 	if unread == 0:
# 		return ""
# 	else:
# 		return unread


# def check_unread_complaints():
# 	""" This returns the number of unread messages """
# 	unread = Complaint.query.filter(Complaint.is_read==False).count()

# 	if unread == 0:
# 		return ""
# 	else:
# 		return unread

@control.context_processor
def main_context():
    """ Include some basic assets in the startup page """
    user = User.query.filter().first()

    return locals()

@control.route('/login/', methods=["GET","POST"])
def login():
    if current_user.is_authenticated:
        flash("Please Logout to Login with an existing account")
        return redirect(url_for('.index', next_url=request.args.get("next", None)))

    page_title = "Log In"

    next_url_ = request.args.get("next_url") or url_for(".index")

    form = LoginForm()
    if form.validate_on_submit():
        data = form.data
        logger.info(data)
        username = data["username"]
        password = data["password"]

        user = authenticate_admin(username, password)
        logger.info(user)

        if user and user.deactivate:
            login_error = "User has been deactivated. Please contact support team."
        else:
            if user is not None:

                login_user(user, remember=True, force=True)  # This is necessary to remember the user

                identity_changed.send(app, identity=Identity(user.id))

                resp = redirect(next_url_)
                user.update_last_login()

                # Transfer auth token to the frontend for use with api requests
                __xcred = base64.b64encode("%s:%s" % (user.username, user.get_auth_token()))

                resp.set_cookie("__xcred", __xcred)

                return resp

            else:
                login_error = "The username or password is invalid"

    return render_template('admin/login.html', **locals())



@control.route('/logout/')
def logout():
    logout_user()

    # Remove session keys set by Flask-Principal
    for key in (
            'identity.name', 'identity.auth_type'):
        session.pop(key, None)

    # Tell Flask-Principal the user is anonymous
    identity_changed.send(app, identity=AnonymousIdentity())

    return redirect(url_for('.login'))


@control.route('/')
def index():
    # user = User.query.filter().first()
    return render_template('admin/index.html', **locals())

@control.route('/staff')
def staff():
    page_title = "Staff Members"
    try:
        page = int(request.args.get("page", 1))
        pages = request.args.get("pages")
        search_q = request.args.get("q", None)
    except:
        abort(404)

    request_args = utils.copy_dict(request.args, {})

    query = User.query.filter(User.is_staff==True).order_by(desc(User.date_created))

    results = query.paginate(page, 20, False)
    if results.has_next:
        # build next page query parameters
        request_args["page"] = results.next_num
        results.next_page = "%s%s" % ("?", urllib.urlencode(request_args))

    if results.has_prev:
        # build previous page query parameters
        request_args["page"] = results.prev_num
        results.previous_page = "%s%s" % ("?", urllib.urlencode(request.args))
    return render_template('admin/staff.html', **locals())


@control.route('/staff/add/')
def add_staff():
    page_title = "Add Staff"
    return render_template('admin/forms/staff.html', **locals())


@control.route('/messages/')
def messages():
    page_title = "Messages"
    try:
        page = int(request.args.get("page", 1))
        pages = request.args.get("pages")
        search_q = request.args.get("q", None)
    except:
        abort(404)

    request_args = utils.copy_dict(request.args, {})

    query = AdminMessage.query.order_by(desc(AdminMessage.date_created))

    results = query.paginate(page, 20, False)
    if results.has_next:
        # build next page query parameters
        request_args["page"] = results.next_num
        results.next_page = "%s%s" % ("?", urllib.urlencode(request_args))

    if results.has_prev:
        # build previous page query parameters
        request_args["page"] = results.prev_num
        results.previous_page = "%s%s" % ("?", urllib.urlencode(request.args))

    return render_template('admin/messages.html', **locals())

@control.route('/messages/sellers/')
def seller_messages():
    page_title = "Messages"
    try:
        page = int(request.args.get("page", 1))
        pages = request.args.get("pages")
        search_q = request.args.get("q", None)
    except:
        abort(404)

    request_args = utils.copy_dict(request.args, {})

    query = AdminMessage.query.order_by(desc(AdminMessage.date_created))

    results = query.paginate(page, 20, False)
    if results.has_next:
        # build next page query parameters
        request_args["page"] = results.next_num
        results.next_page = "%s%s" % ("?", urllib.urlencode(request_args))

    if results.has_prev:
        # build previous page query parameters
        request_args["page"] = results.prev_num
        results.previous_page = "%s%s" % ("?", urllib.urlencode(request.args))

    return render_template('admin/messages.html', **locals())


@control.route('/messages/<int:id>/', methods=['GET','POST'])
def message(id):
    page_title = "Message"
    obj=AdminMessage.query.get(id)
    form = ReplyForm()

    if form.validate_on_submit():
        data = form.data
        data["admin_message_id"]=id
        data["user_id"] = current_user.id
        obj = operations.AdminMessageResponseService.create(**data)
        flash("message successfully replied")
        return redirect(url_for(".messages"))
    return render_template('admin/details/message.html', **locals())


@control.route('/gallery/')
def gallery():
    page_title = "Gallery"

    try:
        page = int(request.args.get("page", 1))
        pages = request.args.get("pages")
        search_q = request.args.get("q", None)
    except:
        abort(404)

    request_args = utils.copy_dict(request.args, {})

    query = Image.query.order_by(desc(Image.date_created))

    results = query.paginate(page, 20, False)
    if results.has_next:
        # build next page query parameters
        request_args["page"] = results.next_num
        results.next_page = "%s%s" % ("?", urllib.urlencode(request_args))

    if results.has_prev:
        # build previous page query parameters
        request_args["page"] = results.prev_num
        results.previous_page = "%s%s" % ("?", urllib.urlencode(request.args))

    return render_template('admin/gallery.html', **locals())



@control.route('/users/')
def users():
    page_title = "Users"
    try:
        page = int(request.args.get("page", 1))
        pages = request.args.get("pages")
        search_q = request.args.get("q", None)
    except:
        abort(404)

    request_args = utils.copy_dict(request.args, {})

    query = User.query.filter(User.is_staff!=True).order_by(desc(User.date_created))

    results = query.paginate(page, 20, False)
    if results.has_next:
        # build next page query parameters
        request_args["page"] = results.next_num
        results.next_page = "%s%s" % ("?", urllib.urlencode(request_args))

    if results.has_prev:
        # build previous page query parameters
        request_args["page"] = results.prev_num
        results.previous_page = "%s%s" % ("?", urllib.urlencode(request.args))
    return render_template('admin/users.html', **locals())


@control.route('/users/create/', methods=["GET", "POST"])
def create_user():
    page_title = "Create User Account"


    return render_template('admin/forms/user.html', **locals())


@control.route('/products/')
def products():
    page_title = "Products"
    try:
        page = int(request.args.get("page", 1))
        pages = request.args.get("pages")
        search_q = request.args.get("q", None)
    except:
        abort(404)

    request_args = utils.copy_dict(request.args, {})

    query = Product.query.order_by(desc(Product.date_created))

    results = query.paginate(page, 20, False)
    if results.has_next:
        # build next page query parameters
        request_args["page"] = results.next_num
        results.next_page = "%s%s" % ("?", urllib.urlencode(request_args))

    if results.has_prev:
        # build previous page query parameters
        request_args["page"] = results.prev_num
        results.previous_page = "%s%s" % ("?", urllib.urlencode(request.args))

    return render_template('admin/messages.html', **locals())


