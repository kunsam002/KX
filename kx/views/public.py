"""
public.py

@Author: Ogunmokun, Olukunle

The public views required to sign up and get started
"""

from flask import Blueprint, render_template, abort, redirect, \
    flash, url_for, request, session, g, make_response, current_app
from flask_login import logout_user, login_required, login_user, current_user
from kx import db, logger, app
from kx.forms import *
from kx.services import *
from kx.services import users, site_services
from kx.services.authentication import authenticate_user
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
from flask.ext.principal import Principal, Identity, AnonymousIdentity, identity_changed, PermissionDenied
import base64
import requests
import xmltodict
import os
import sys
import random
import pprint
import cgi

www = Blueprint('public', __name__)


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


def object_length(data):
    return len(data)


@www.context_processor
def main_context():
    """ Include some basic assets in the startup page """
    today = date.today()
    minimum = min
    string = str
    number_format = utils.number_format
    length = object_length
    join_list = utils.join_list
    slugify = utils.slugify
    paging_url_build = build_page_url
    clean_ascii = utils.clean_ascii
    login_form = LoginForm()

    return locals()


@www.route('/login/', methods=["POST"])
def login():
    if current_user.is_authenticated:
        flash("Please Logout to Login with an existing account")
        return redirect(url_for('.index', next_url=request.args.get("next", None)))

    page_title = "Log In"

    next_url_ = request.args.get("next_url") or url_for(".index")

    form = LoginForm()
    if form.validate_on_submit():
        data = form.data
        username = data["username"]
        password = data["password"]

        user = authenticate_user(username, password)

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

    return render_template("login.html", **locals())


@www.route('/signup/', methods=["GET", "POST"])
def signup():
    page_title = "Signup"
    next_url_ = request.args.get("next_url") or url_for(".index")

    form = SignupForm()
    if form.validate_on_submit():
        data = form.data
        user = users.UserService.create(**data)

        login_user(user, remember=True, force=True)  # This is necessary to remember the user

        identity_changed.send(app, identity=Identity(user.id))

        resp = redirect(next_url_)

        # Transfer auth token to the frontend for use with api requests
        __xcred = base64.b64encode("%s:%s" % (user.username, user.get_auth_token()))

        resp.set_cookie("__xcred", __xcred)

        return resp

    return render_template("public/signup.html", **locals())


@www.route('/<string:path>/')
@www.route('/')
def index(path=None):
    products = site_services.fetch_top_view_products()
    states = site_services.fetch_states()
    universities = site_services.fetch_universities()

    form = SearchForm()
    form.state_id.choices = [(0,"--- Select One ---")] + [(i.id,i.name) for i in states]
    form.university_id.choices = [(0,"--- Select One ---")] + [(i.id,i.name) for i in universities]
    form.section_id.choices = [(0,"--- Select One ---")] + [(i.id,i.name) for i in Section.query.all()]
    form.category_id.choices = [(0,"--- Select One ---")] + [(i.id,i.name) for i in Category.query.all()]

    sections = Section.query.order_by(Section.name).all()

    return render_template("public/index.html", **locals())


# @www.route('/categories/', methods=["GET", "POST"])
# def categories():
#     page_title = "Categories"
#
#     states = site_services.fetch_states()
#     universities = site_services.fetch_universities()
#
#     form = SearchForm()
#     form.state_id.choices = [(0,"--- Select One ---")] + [(i.id,i.name) for i in states]
#     form.university_id.choices = [(0,"--- Select One ---")] + [(i.id,i.name) for i in universities]
#     form.section_id.choices = [(0,"--- Select One ---")] + [(i.id,i.name) for i in Section.query.all()]
#     form.category_id.choices = [(0,"--- Select One ---")] + [(i.id,i.name) for i in Category.query.all()]
#     return render_template("public/listing.html", **locals())


@www.route('/products/<string:section_slug>/<category_slug>/', methods=["GET", "POST"])
@www.route('/products/<string:section_slug>/', methods=["GET", "POST"])
@www.route('/products/', methods=["GET", "POST"])
def categories(section_slug=None, category_slug=None):
    page_title = "Products"

    return render_template("public/listing.html", **locals())
