"""
public.py

@Author: Ogunmokun, Olukunle

The public views required to sign up and get started
"""

from flask import Blueprint, render_template, abort, redirect, \
    flash, url_for, request, session, g, make_response, current_app, jsonify
from flask_login import logout_user, login_required, login_user, current_user
from kx import db, logger, app, handle_uploaded_photos
from kx.forms import *
from kx.services import *
from kx.services import users, site_services, operations
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
from flask_principal import Principal, Identity, AnonymousIdentity, identity_changed, PermissionDenied
import base64
import requests
import xmltodict
import os
import sys
import random
from pprint import pprint
import cgi

www = Blueprint('public', __name__, template_folder='../templates', static_folder='/kx/static')


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


def _split_flash(msg):
    logger.info(msg)
    logger.info(msg.split("|"))
    return msg.split("|")


def prepare_search_data(form):
    """ Cleans up search data from the request query and handles it for validation """
    res = form.validate()
    data = form.data
    if not res:
        data = form.data
    for x in form.errors.keys():
        data[x] = getattr(form, x).default

    return data


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
    join_list = utils.join_list
    paging_url_build = build_page_url
    clean_ascii = utils.clean_ascii
    login_form = LoginForm()
    split_flash_message = _split_flash

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

    return redirect(next_url_)


@www.route('/signup/', methods=["GET", "POST"])
def signup():
    page_title = "Signup"
    next_url_ = request.args.get("next_url") or url_for(".index")

    form = SignupForm()
    if form.validate_on_submit():
        data = form.data
        user= users.UserService.create(**data)

        _data = {"name": "General"}

        user = User.query.filter(User.email == data.get("email", "")).first()
        users.UserService.create_wishlist(user.id, **_data)

        login_user(user, remember=True, force=True)  # This is necessary to remember the user

        identity_changed.send(app, identity=Identity(user.id))

        resp = redirect(next_url_)

        # Transfer auth token to the frontend for use with api requests
        __xcred = base64.b64encode("%s:%s" % (user.username, user.get_auth_token()))

        resp.set_cookie("__xcred", __xcred)

        return resp

    return render_template("public/signup.html", **locals())


@www.route('/logout/')
def logout():
    logout_user()

    # Remove session keys set by Flask-Principal
    for key in (
            'identity.name', 'identity.auth_type'):
        session.pop(key, None)

    # Tell Flask-Principal the user is anonymous
    identity_changed.send(app, identity=AnonymousIdentity())

    return redirect(url_for('.index'))


@www.route('/fetch/section_categories/', methods=['GET', 'POST'])
def fetch_dir_section_cats():
    if request.method == "POST":
        _data = request.data
        if not _data:
            response = make_response("Request Method not Allowed")
            return response

        try:
            id = int(_data)
            section = Section.query.get(id)

            _refine = []
            for i in section.categories:
                refine = {}
                refine["id"], refine["name"] = i.id, i.name
                _refine.append(refine)

            refine = json.dumps(_refine)
            response = make_response(refine)
            return response
        except Exception as e:
            print "---------Error: %s-----------" % str(e)
            logger.info("---------Error: %s-----------" % str(e))
            msg = "Failed with Error " + str(e)
            response = make_response(msg)
            return response

    else:
        response = make_response("Request Method not Allowed")
        return response


@www.route('/<string:path>/')
@www.route('/')
def index(path=None):
    universities = site_services.fetch_universities()

    form = SearchForm()
    form.product_type.choices = [(0, "--- Select One ---")] + [(i.id, i.name) for i in ProductType.query.all()]
    form.university_id.choices = [(0, "--- Select One ---")] + [(i.id, i.name) for i in universities]
    form.sec_id.choices = [(0, "--- Select One ---")] + [(i.id, i.name) for i in Section.query.all()]
    form.cat_id.choices = [(0, "--- Select One ---")] + [(i.id, i.name) for i in Category.query.all()]

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
def products(section_slug=None, category_slug=None):
    page_title = "Products"

    products = site_services.fetch_top_view_products()
    universities = site_services.fetch_universities()

    form = SearchForm()
    form.product_type.choices = [(0, "--- Select One ---")] + [(i.id, i.name) for i in ProductType.query.all()]
    form.university_id.choices = [(0, "--- Select One ---")] + [(i.id, i.name) for i in universities]
    form.sec_id.choices = [(0, "--- Select One ---")] + [(i.id, i.name) for i in Section.query.all()]
    form.cat_id.choices = [(0, "--- Select One ---")] + [(i.id, i.name) for i in Category.query.all()]

    return render_template("public/products.html", **locals())


@www.route('/search-results/', methods=["GET", "POST"])
def search_results():
    page_title = "Search results"

    """ handles the search by composing the filters and query to make the results. Currently searching products/shops """

    try:
        pages = request.args.get("pages")
        page = int(request.args.get("page", 1))
        size = abs(int(request.args.get("size", 30)))
        search_q = request.args.get("q", None)
    except:
        abort(404)

    products = site_services.fetch_top_view_products()
    universities = site_services.fetch_universities()

    form = SearchForm()
    form.product_type.choices = [(0, "--- Select One ---")] + [(i.id, i.name) for i in ProductType.query.all()]
    form.university_id.choices = [(0, "--- Select One ---")] + [(i.id, i.name) for i in universities]
    form.sec_id.choices = [(0, "--- Select One ---")] + [(i.id, i.name) for i in Section.query.all()]
    form.cat_id.choices = [(0, "--- Select One ---")] + [(i.id, i.name) for i in Category.query.all()]

    request_args = utils.copy_dict(form.data, {})
    logger.info(request_args)
    # form = PageFilterForm(request_args, csrf_enabled=False)
    # search_data = prepare_search_data(form)

    # page = search_data['page']
    # order_by = search_data['order_by']
    # tag_id = search_data['tag_id']
    # search_q = search_data['q']


    query = Product.query.filter(Product.is_enabled == True).order_by(
        desc(Product.date_created))

    if search_q:
        queries = [Product.name.ilike("%%%s%%" % search_q)]
        query = query.filter(or_(*queries))

    results = query.paginate(page, 20, False)
    if results.has_next:
        # build next page query parameters
        request_args["page"] = results.next_num
        results.next_page = "%s%s" % ("?", urllib.urlencode(request.args))

    if results.has_prev:
        # build previous page query parameters
        request_args["page"] = results.prev_num
        results.previous_page = "%s%s" % ("?", urllib.urlencode(request.args))

    return render_template("public/search-results.html", **locals())


@www.route('/products/<int:id>/<string:sku>/', methods=['GET', 'POST'])
def product(id, sku):
    page_title = "Product"

    obj = Product.query.filter(Product.sku == sku).first()
    user_id = None
    if current_user.is_authenticated:
        user_id = current_user.id
        message_form = MessageForm(obj=current_user, name=current_user.full_name, product_id=obj.id)
    else:
        message_form = MessageForm(product_id=obj.id, user_id=user_id)

    review_form = ProductReviewForm(product_id=obj.id, user_id=user_id)
    if message_form.validate_on_submit():
        data = message_form.data
        data["user_id"]=user_id
        data["seller_id"] = obj.user_id
        pprint(data)
        review = operations.MessageService.create(**data)
        return redirect(url_for('.product', id=id, sku=sku))

    return render_template("public/product.html", **locals())


@www.route('/products/<int:id>/<string:sku>/create_review/', methods=['GET', 'POST'])
def product_review(id, sku):
    page_title = "Product"

    obj = Product.query.filter(Product.sku == sku).first()
    user_id = None
    if current_user.is_authenticated:
        user_id = current_user.id

    review_form = ProductReviewForm(product_id=obj.id, user_id=user_id)
    if review_form.validate_on_submit():
        data = review_form.data
        review = operations.ProductReviewService.create(**data)

    return redirect(url_for('.product', id=obj.user_id, sku=obj.sku))


# Profile View Functions Start >>>>>>>

@www.route('/profile/')
@login_required
def profile():
    if current_user.is_authenticated:
        welcome_note = "%s" % current_user.username if current_user.username else "%s" % current_user.first_name
    else:
        welcome_note = "Profile"
    return render_template("public/profile/index.html", **locals())


@www.route('/profile/my_products/')
@login_required
def profile_products():
    page_title = "My Products"

    try:
        page = int(request.args.get("page", 1))
        pages = request.args.get("pages")
        search_q = request.args.get("q", None)
    except:
        abort(404)

    request_args = utils.copy_dict(request.args, {})

    query = Product.query.filter(Product.user_id == current_user.id).order_by(desc(Product.date_created))

    results = query.paginate(page, 20, False)
    if results.has_next:
        # build next page query parameters
        request_args["page"] = results.next_num
        results.next_page = "%s%s" % ("?", urllib.urlencode(request_args))

    if results.has_prev:
        # build previous page query parameters
        request_args["page"] = results.prev_num
        results.previous_page = "%s%s" % ("?", urllib.urlencode(request.args))
    return render_template("public/profile/products.html", **locals())


@www.route('/profile/my_products/create/', methods=['GET', 'POST'])
@login_required
def create_product():
    page_title = "Create Product"

    files = request.files.getlist("images")

    # Test for the first entry
    empty_files = False
    for _f in files:
        if _f.filename == '' or utils.check_extension(_f.filename) is False:
            empty_files = True
            break

    create_product_form = ProductForm()
    create_product_form.section_id.choices = [(0, "--- Select One ---")] + [(i.id, i.name) for i in Section.query.all()]
    create_product_form.category_id.choices = [(0, "--- Select One ---")] + [(i.id, i.name) for i in
                                                                             Category.query.all()]
    pprint(create_product_form.errors)
    pprint(create_product_form.data)
    pprint(files)
    if create_product_form.validate_on_submit() and empty_files is False:

        uploaded_files, errors = handle_uploaded_photos(files, (160, 160))

        if uploaded_files:

            data = create_product_form.data
            data["user_id"] = current_user.id
            data["description"] = str(data.get("description"))

            product = operations.ProductService.create(**data)

            images = []
            for upload_ in uploaded_files:
                img = operations.ImageService.create(product_id=product.id, **upload_)
                images.append(img)
                _d_ = {"cover_image_id": img.id}
                product = operations.ProductService.set_cover_image(product.id, **_d_)

            if len(images) < 1:
                operations.ProductService.delete(product.id)

            flash("Product successfully created. Please wait 24hours for Product display Approval")
            _next = url_for(".profile_products")
            current_user.is_seller=True
            db.session.add(current_user)
            db.session.commit()
            return redirect(_next)
        else:
            img_errors = "At least one image is required per product"

            # From SME
            # uploaded_files, errors = handle_uploaded_photos(files, (160, 160))
            #
            # if uploaded_files:
            #     data = create_product_form.data
            #     data["user_id"] = current_user.id
            #     data["_price"] = data["price"]
            #     data["product_type"] = "Product"
            #     data["_compare_at"] = data["compare_at"]
            #     obj = operations.ProductService.create(**data)
            #
            #     if obj:
            #         for _d in uploaded_files:
            #             _d["alt_text"] = obj.name
            #             try:
            #                 img = operations.ImageService.create(product_id=product.id, **_d)
            #             except:
            #                 operations.ProductService.delete(obj.id)
            #                 create_product_form.errors["images"] = errors
            #                 raise
            #
            #         flash("Product successfully created. Please wait 24hours for Product display Approval")
            #         _next = url_for(".products", shop_id=obj.shop.id)
            #         return redirect(_next)
            # else:
            #     img_errors = "At least one image is required per product"

    return render_template("public/profile/create_product.html", **locals())


@www.route('/profile/my_product/<string:sku>/update/', methods=['GET', 'POST'])
@login_required
def update_product(sku):
    page_title = "Create Product"

    obj = Product.query.filter(Product.sku == sku, Product.user_id == current_user.id).first()

    files = request.files.getlist("images")
    next_url = request.args.get("next_url") or url_for(".profile_products")

    # Test for the first entry
    empty_files = False
    for _f in files:
        if _f.filename == '' or utils.check_extension(_f.filename) is False:
            empty_files = True
            break

    existing_images = obj.images.all()

    create_product_form = UpdateProductForm(obj=obj, data={"cover_image_id": obj.cover_image_id})
    create_product_form.section_id.choices = [(0, "--- Select One ---")] + [(i.id, i.name) for i in Section.query.all()]
    create_product_form.category_id.choices = [(0, "--- Select One ---")] + [(i.id, i.name) for i in
                                                                             Category.query.all()]
    create_product_form.removables.choices = [(0, "---- Select One ----")] + [(l.id, l.name) for l in existing_images]
    if create_product_form.validate_on_submit():
        data = create_product_form.data
        removables = data.pop("removables", [])
        obj_ = operations.ProductService.update(obj.id, **data)
        if obj_:
            # If files are present, attach them to the product images
            if empty_files is False:
                uploaded_files, errors = handle_uploaded_photos(files, (160, 160))
                if uploaded_files:
                    for _d in uploaded_files:
                        _d["alt_text"] = obj_.name
                        img = operations.ImageService.create(product_id=obj.id, **_d)

            for _img_id in removables:
                if obj_.cover_image_id != _img_id:
                    operations.ImageService.delete(_img_id)

            flash("Product successfully updated")
            return redirect(next_url)

    return render_template("public/profile/create_product.html", **locals())


@www.route('/profile/messages/')
@login_required
def profile_messages():
    welcome_note = "Kampus Xchange"
    try:
        page = int(request.args.get("page", 1))
        pages = request.args.get("pages")
        search_q = request.args.get("q", None)
    except:
        abort(404)

    request_args = utils.copy_dict(request.args, {})

    query = AdminMessage.query.filter(AdminMessage.user_id == current_user.id).order_by(desc(AdminMessage.date_created))

    results = query.paginate(page, 20, False)
    if results.has_next:
        # build next page query parameters
        request_args["page"] = results.next_num
        results.next_page = "%s%s" % ("?", urllib.urlencode(request_args))

    if results.has_prev:
        # build previous page query parameters
        request_args["page"] = results.prev_num
        results.previous_page = "%s%s" % ("?", urllib.urlencode(request.args))

    return render_template("public/profile/messages.html", **locals())

@www.route('/profile/messages/<int:id>/response/', methods=["GET","POST"])
@login_required
def profile_message_response(id):
    obj = AdminMessage.query.get(id)
    if not obj:
        abort(404)
    try:
        page = int(request.args.get("page", 1))
        pages = request.args.get("pages")
        search_q = request.args.get("q", None)
    except:
        abort(404)


    request_args = utils.copy_dict(request.args, {})

    is_cust = False

    query = AdminMessage.query.filter(AdminMessage.user_id == current_user.id).order_by(desc(AdminMessage.date_created))

    results = query.paginate(page, 20, False)
    if results.has_next:
        # build next page query parameters
        request_args["page"] = results.next_num
        results.next_page = "%s%s" % ("?", urllib.urlencode(request_args))

    if results.has_prev:
        # build previous page query parameters
        request_args["page"] = results.prev_num
        results.previous_page = "%s%s" % ("?", urllib.urlencode(request.args))

    reply_form = ReplyForm()
    if reply_form.validate_on_submit():
        data = reply_form.data
        data["admin_message_id"]=id
        data["user_id"] = current_user.id
        reply = operations.AdminMessageResponseService.create(**data)
        return redirect(url_for('.profile_message_response',id=id))
    return render_template("public/profile/message_response.html", **locals())


@www.route('/profile/customer_messages/')
@login_required
def profile_cust_messages():
    welcome_note = "Customers"
    try:
        page = int(request.args.get("page", 1))
        pages = request.args.get("pages")
        search_q = request.args.get("q", None)
    except:
        abort(404)

    request_args = utils.copy_dict(request.args, {})

    query = Message.query.filter(Message.seller_id == current_user.id).order_by(desc(Message.date_created))

    results = query.paginate(page, 20, False)
    if results.has_next:
        # build next page query parameters
        request_args["page"] = results.next_num
        results.next_page = "%s%s" % ("?", urllib.urlencode(request_args))

    if results.has_prev:
        # build previous page query parameters
        request_args["page"] = results.prev_num
        results.previous_page = "%s%s" % ("?", urllib.urlencode(request.args))

    return render_template("public/profile/cust_messages.html", **locals())

@www.route('/profile/customer_messages/<int:id>/response/', methods=["GET","POST"])
@login_required
def profile_cust_message_response(id):

    obj = Message.query.get(id)
    if not obj:
        abort(404)
    logger.info(obj)
    try:
        page = int(request.args.get("page", 1))
        pages = request.args.get("pages")
        search_q = request.args.get("q", None)
    except:
        abort(404)
    request_args = utils.copy_dict(request.args, {})
    is_cust = True

    query = Message.query.filter(Message.seller_id == current_user.id).order_by(desc(Message.date_created))

    results = query.paginate(page, 20, False)
    if results.has_next:
        # build next page query parameters
        request_args["page"] = results.next_num
        results.next_page = "%s%s" % ("?", urllib.urlencode(request_args))

    if results.has_prev:
        # build previous page query parameters
        request_args["page"] = results.prev_num
        results.previous_page = "%s%s" % ("?", urllib.urlencode(request.args))

    reply_form = ReplyForm()
    if reply_form.validate_on_submit():
        data = reply_form.data
        data["message_id"]=id
        data["user_id"] = current_user.id
        reply = operations.MessageResponseService.create(**data)
        return redirect(url_for('.profile_cust_message_response',id=id))
    return render_template("public/profile/message_response.html", **locals())



@www.route('/profile/settings/', methods=['GET', 'POST'])
@login_required
def profile_settings():
    page_title = "Settings"
    logger.info(current_user)
    update_profile_form = ProfileUpdateForm(obj=current_user)
    update_profile_form.university_id.choices = [(0, "--- Select One ---")] + [(i.id, i.name) for i in
                                                                               University.query.filter(
                                                                                   University.is_enabled == True).all()]
    password_reset_form = PasswordResetForm()

    return render_template("public/profile/settings.html", **locals())


@www.route('/profile/settings/update/', methods=['GET', 'POST'])
@login_required
def profile_update():
    update_profile_form = ProfileUpdateForm()
    update_profile_form.university_id.choices = [(0, "--- Select One ---")] + [(i.id, i.name) for i in
                                                                               University.query.filter(
                                                                                   University.is_enabled == True).all()]
    flash("info|message")

    if update_profile_form.validate_on_submit():
        data = update_profile_form.data
        user = users.UserService.update(current_user.id, **data)
        flash("Profile Update Successful")

    return redirect(url_for('.profile_settings'))


@www.route('/profile/settings/password_reset/', methods=['GET', 'POST'])
@login_required
def profile_password_reset():
    password_reset_form = PasswordResetForm()
    flash("info|message")

    if password_reset_form.validate_on_submit():
        data = password_reset_form.data
        user = users.UserService.reset_password(current_user.id, **data)
        flash("Password Reset Successful")

    return redirect(url_for('.profile_settings'))


# <<<<<<<<< Profile View functions end

@www.route('/contact/', methods=['GET', 'POST'])
def contact():
    page_title = "Contact Us"
    user_id = None
    if current_user.is_authenticated:
        user_id = current_user.id
        contact_form = ContactForm(obj=current_user, user_id=user_id, name=current_user.full_name)
    else:
        contact_form = ContactForm()

    if contact_form.validate_on_submit():
        data = contact_form.data
        data["user_id"] = user_id
        msg = operations.AdminMessageService.create(**data)
        flash("Message Successful")

    return render_template("public/contact.html", **locals())


@www.route('/contact/sending/', methods=['GET', 'POST'])
def contact_sending():
    page_title = "Contact Us"
    if request.method == "POST":
        _data = {}
        if request.data:
            _data = request.data
            _data = json.loads(_data)
        elif request.form:
            _data = json.dumps(request.form)
            _data = json.loads(_data)
        logger.info(_data)
        contact_form = ContactForm(obj=_data)
        if contact_form.validate_on_submit():
            data = contact_form.data
            u = User.query.filter(User.email == data.get("email")).first()
            if u:
                data["user_id"] = u.id
            msg = operations.AdminMessageService.create(**data)

            _data = {"status": "success", "message": "Message Sent successfully"}
            data = jsonify(_data)
            response = make_response(data)
            response.headers['Content-Type'] = "application/json"
            return response
        else:
            logger.info(contact_form.errors)
            _data = {"status": "failure", "message": "Form Validation failed"}
            data = jsonify(_data)
            response = make_response(data)
            response.headers['Content-Type'] = "application/json"
            return response

    else:
        data = {"Status": "failure", "message": "Request Method not Allowed"}
        data = jsonify(data)
        response = make_response(data)
        response.headers['Content-Type'] = "application/json"
        return response


@www.route('/blog/')
def blog():
    page_title = "Blog"
    return render_template("public/blog/index.html", **locals())
