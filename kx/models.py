# Models

from kx import bcrypt, app, logger
db = app.db
from kx.core.utils import slugify, id_generator
from flask_login import UserMixin
from sqlalchemy import or_
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method, Comparator
from sqlalchemy.inspection import inspect
from datetime import datetime, timedelta
import hashlib
from sqlalchemy import func, asc, desc
from sqlalchemy import inspect, UniqueConstraint, desc
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.collections import InstrumentedList
from sqlalchemy.orm import dynamic
from flask import url_for
import inspect as pyinspect
from socket import gethostname, gethostbyname



# SQLAlchemy Continuum
# import sqlalchemy as sa
# from sqlalchemy_continuum.ext.flask import FlaskVersioningManager
# from sqlalchemy_continuum import make_versioned

# make_versioned(manager=FlaskVersioningManager())


def get_model_from_table_name(tablename):
    """ return the Model class for a given __tablename__ """

    _models = [args[1] for args in globals().items() if pyinspect.isclass(args[
                                                                              1]) and issubclass(args[1], db.Model)]

    for _m in _models:
        try:
            if _m.__tablename__ == tablename:
                return _m
        except Exception, e:
            logger.info(e)
            raise

    return None


def slugify_from_name(context):
    """
    An sqlalchemy processor that works with default and onupdate
    field parameters to automatically slugify the name parameters in the model
    """
    return slugify(context.current_parameters['name'])


def generate_user_token_code(context):
    return hashlib.md5("%s:%s:%s" % (
        context.current_parameters["user_id"], context.current_parameters["email"], str(datetime.now()))).hexdigest()


class AppMixin(object):
    """ Mixin class for general attributes and functions """

    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    # __versioned__ = {} # SQLAlchemy Continuum

    @declared_attr
    def is_deleted(cls):
        return db.Column(db.Boolean, default=False)

    @declared_attr
    def date_created(cls):
        return db.Column(db.DateTime, default=datetime.utcnow)

    @declared_attr
    def last_updated(cls):
        return db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def as_full_dict(self):
        """ Retrieve all values of this model as a dictionary """
        data = inspect(self)

        return dict([(k, getattr(self, k)) for k in data.attrs.keys()])

    def as_dict(self, include_only=None, exclude=[], extras=[]):
        """ Retrieve all values of this model as a dictionary """

        data = inspect(self)
        if include_only is None:
            include_only = data.attrs.keys()

        return dict([(k, getattr(self, k)) for k in data.attrs.keys() + extras
                     if k in include_only + extras and isinstance(getattr(self, k), (
                db.Model, db.Query, InstrumentedList, dynamic.AppenderMixin)) is False
                     and k not in exclude])

    def as_dict_inner(self, include_only=None, exclude=["is_deleted"], extras=[], child=None, child_include=[]):
        """ Retrieve all values of this model as a dictionary """
        data = inspect(self)

        if include_only is None:
            include_only = data.attrs.keys() + extras

        else:
            include_only = include_only + extras

        _dict = dict([(k, getattr(self, k)) for k in include_only if isinstance(getattr(self, k),
                                                                                (hybrid_property, InstrumentedAttribute,
                                                                                 InstrumentedList,
                                                                                 dynamic.AppenderMixin)) is False and k not in exclude])

        for key, obj in _dict.items():
            if isinstance(obj, db.Model):
                _dict[key] = obj.as_dict()

            if isinstance(obj, (list, tuple)):
                items = []
                for item in obj:
                    inspect_item = inspect(item)
                    items.append(
                        dict([(k, getattr(item, k)) for k in inspect_item.attrs.keys() + extras if
                              k not in exclude and hasattr(item, k)]))

                for item in items:
                    obj = item.get(child)
                    if obj:
                        item[child] = obj.as_dict(extras=child_include)
        return _dict


class UserMixin(AppMixin, UserMixin):
    """ Mixin class for User related attributes and functions """

    @declared_attr
    def user_id(cls):
        return db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)

    @property
    def user(self):
        if self.user_id:
            return User.query.get(self.user_id)
        else:
            return None


class City(AppMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    code = db.Column(db.String(200), index=True)
    state_id = db.Column(db.Integer, db.ForeignKey('state.id'), nullable=False, index=True)
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'), nullable=False, index=True)


class State(AppMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    slug = db.Column(db.String(200), unique=True, default=slugify_from_name, onupdate=slugify_from_name, index=True)
    code = db.Column(db.String(200), index=True)
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'), nullable=False, index=True)
    cities = db.relationship('City', backref='state', lazy='dynamic')
    universities = db.relationship('University', backref='state', lazy='dynamic')


class Country(AppMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    slug = db.Column(db.String(200), unique=True, default=slugify_from_name, index=True)
    code = db.Column(db.String(200), index=True)
    enabled = db.Column(db.Boolean, default=False, index=True)
    states = db.relationship('State', backref='country', lazy='dynamic')
    cities = db.relationship('City', backref='country', lazy='dynamic')


class Timezone(AppMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), index=True)
    code = db.Column(db.String(200), index=True)
    offset = db.Column(db.String(200))  # UTC time


class Currency(AppMixin, db.Model):
    __searchable__ = True

    __include_in_index__ = ["name", "code",
                            "enabled", "symbol", "payment_code"]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), index=True)
    code = db.Column(db.String(200), index=True)
    enabled = db.Column(db.Boolean, default=False, index=True)
    symbol = db.Column(db.String(200), index=True)
    payment_code = db.Column(db.String(200), index=True)

    def __unicode__(self):
        return "%s (%s)" % (self.name.title(), self.code)

    def __repr__(self):
        return '<Currency %r>' % self.name


class Image(AppMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=False)
    alt_text = db.Column(db.String(200), unique=False)
    url = db.Column(db.String(200), unique=False, index=True)
    width = db.Column(db.Float)
    height = db.Column(db.Float)
    product_id = db.Column(
        db.Integer, db.ForeignKey('product.id'), nullable=True, index=True)
    section_id = db.Column(
        db.Integer, db.ForeignKey('section.id'), nullable=True, index=True)
    banner_id = db.Column(
        db.Integer, db.ForeignKey('banner.id'), nullable=True, index=True)
    type = db.Column(db.String(200), nullable=True)

    def delete_file(self):
        """ Deletes the actual image file from disk """
        raise NotImplementedError()

    @property
    def cover_image(self):
        return self

    def __repr__(self):
        return '<Image %r>' % self.name


class Message(AppMixin, db.Model):
    __searchable__ = True

    __include_in_index__ = ["name", "email", "phone", "subject", "url", "is_read",
                            "has_parent", "user_read", "is_replied", "date_replied", "body", "responses"]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False, index=True)
    phone = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.Text)
    url = db.Column(db.Text, nullable=True)
    is_read = db.Column(db.Boolean, default=False, index=True)
    has_parent = db.Column(db.Boolean, default=False)
    user_read = db.Column(db.Boolean, default=False, index=True)
    is_replied = db.Column(db.Boolean, default=False, index=True)
    date_replied = db.Column(db.DateTime, nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, index=True)
    body = db.Column(db.Text)  # for plain text messages
    responses = db.relationship(
        'MessageResponse', backref='message', lazy='dynamic', cascade="all,delete-orphan")


class MessageResponse(AppMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(
        db.Integer, db.ForeignKey('message.id'), nullable=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    body = db.Column(db.Text)  # for plain text messages


class AdminMessage(AppMixin, db.Model):
    __searchable__ = True

    __include_in_index__ = ["name", "email", "phone", "subject", "is_read", "has_parent",
                            "user_read", "is_replied", "date_replied", "body", "responses", "user_id"]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False, index=True)
    phone = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False, index=True)
    user_read = db.Column(db.Boolean, default=False, index=True)
    has_parent = db.Column(db.Boolean, default=False)
    is_replied = db.Column(db.Boolean, default=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
    date_replied = db.Column(db.DateTime, nullable=True)
    body = db.Column(db.Text)  # for plain text messages
    responses = db.relationship(
        'AdminMessageResponse', backref='admin_message', lazy='dynamic', cascade="all,delete-orphan")


class AdminMessageResponse(AppMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_message_id = db.Column(db.Integer, db.ForeignKey(
        'admin_message.id'), nullable=False, index=True)
    body = db.Column(db.Text)  # for plain text messages
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)


class User(db.Model, UserMixin, AppMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), unique=True, index=True)
    email = db.Column(db.String(200), unique=True, index=True)
    first_name = db.Column(db.String(200), unique=False)
    last_name = db.Column(db.String(200), unique=False)
    full_name = db.Column(db.String(200), unique=False)
    password = db.Column(db.Text, unique=False)
    active = db.Column(db.Boolean, default=False)
    is_confirmed = db.Column(db.Boolean, default=False, index=True)
    is_staff = db.Column(db.Boolean, default=False, index=True)
    is_global = db.Column(db.Boolean, default=False, index=True)
    is_super_admin = db.Column(db.Boolean, default=False)
    deactivate = db.Column(db.Boolean, default=False)
    gender = db.Column(db.String(200))
    location = db.Column(db.String(200))
    dob = db.Column(db.DateTime)
    phone = db.Column(db.String(200))
    login_count = db.Column(db.Integer, default=0)
    last_login_at = db.Column(db.DateTime)
    current_login_at = db.Column(db.DateTime)
    last_login_ip = db.Column(db.String(200))
    current_login_ip = db.Column(db.String(200))
    university_id = db.Column(db.Integer, db.ForeignKey('university.id'), nullable=True, index=True)
    products = db.relationship(
        'Product', backref='user', lazy='dynamic', cascade="all,delete-orphan")

    def update_last_login(self):
        if self.current_login_at is None and self.last_login_at is None:
            self.current_login_at = self.last_login_at = datetime.now()
            self.current_login_ip = self.last_login_ip = gethostbyname(gethostname())

        if self.current_login_at != self.last_login_at:
            self.last_login_at = self.current_login_at
            self.last_login_ip = self.current_login_ip
            self.current_login_at = datetime.now()
            self.current_login_ip = gethostbyname(gethostname())

        if self.last_login_at == self.current_login_at:
            self.current_login_at = datetime.now()
            self.current_login_ip = gethostbyname(gethostname())

        self.login_count += 1
        db.session.add(self)
        db.session.commit()

    @hybrid_property
    def roles(self):
        """ Fetch user roles as a list of roles """
        roles = []
        for access_group in self.access_groups:
            for role in access_group.roles:
                roles.append(role)

        return list(set(roles))

    def __repr__(self):
        return '<User %r>' % self.username

    def get_auth_token(self):
        """ Returns the user's authentication token """
        return hashlib.md5("%s:%s" % (self.username, self.password)).hexdigest()

    def is_active(self):
        """ Returns if the user is active or not. Overriden from UserMixin """
        return self.active

    def generate_password(self, password):
        """
        Generates a password from the plain string

        :param password: plain password string
        """

        self.password = bcrypt.generate_password_hash(password)

    def check_password(self, password):
        """
        Checks the given password against the saved password

        :param password: password to check
        :type password: string

        :returns True or False
        :rtype: bool

        """
        return bcrypt.check_password_hash(self.password, password)

    def set_password(self, new_password):
        """
        Sets a new password for the user

        :param new_password: the new password
        :type new_password: string
        """

        self.generate_password(new_password)
        db.session.add(self)
        db.session.commit()

        # def add_role(self, role):
        #     """
        #     Adds a the specified role to the user
        #     :param role: Role ID or Role name or Role object to be added to the user
        #
        #     """
        #     try:
        #
        #         if isinstance(role, Role) and hasattr(role, "id"):
        #             role_obj = role
        #         elif type(role) is int:
        #             role_obj = Role.query.get(role)
        #         elif type(role) is str:
        #             role_obj = Role.query.filter(Role.name == role.lower()).one()
        #
        #         if not role_obj:
        #             raise Exception("Specified role could not be found")
        #
        #         if self.has_role(role_obj) is False:
        #             self.roles.append(role_obj)
        #             db.session.add(self)
        #             db.session.commit()
        #             return self
        #     except:
        #         db.session.rollback()
        #         raise
        #
        # def has_role(self, role):
        #     """
        #     Returns true if a user identifies with a specific role
        #
        #     :param role: A role name or `Role` instance
        #     """
        #     return role in self.roles
        #
        # # def add_access_group(self, access_group):
        # #     """
        # #     Adds a the specified access group to the user
        # #     :param group: AccessGroup ID or AccessGroup name or AccessGroup object to be added to the user
        # #
        # #     """
        # #     try:
        # #
        # #         if isinstance(access_group, AccessGroup) and hasattr(access_group, "id"):
        # #             group_obj = access_group
        # #         elif type(access_group) is int:
        # #             group_obj = AccessGroup.query.get(access_group)
        # #         elif type(access_group) is str:
        # #             group_obj = AccessGroup.query.filter(
        # #                 AccessGroup.name == access_group.lower()).one()
        # #
        # #         if not group_obj:
        # #             raise Exception("Specified access_group could not be found")
        # #
        # #         if self.has_access_group(group_obj) is False:
        # #             self.access_groups.append(group_obj)
        # #             db.session.add(self)
        # #             db.session.commit()
        # #             return self
        # #     except:
        # #         db.session.rollback()
        # #         raise
        # #
        # # def has_access_group(self, access_group):
        # #     """
        # #     Returns true if a user identifies with a specific access_group
        # #
        # #     :param access_group: A access_group name or `AccessGroup` instance
        # #     """
        # #     return access_group in self.access_groups


class University(AppMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=False, nullable=False)
    handle = db.Column(db.String(200), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    about_information = db.Column(db.Text)  # information for your about page
    thumbnail = db.Column(db.Text)  # storefront thumbnail url
    logo = db.Column(db.Text)  # storefront thumbnail url
    city_id = db.Column(db.Integer, db.ForeignKey('city.id'), nullable=True, index=True)
    is_enabled = db.Column(db.Boolean, default=False)
    state_id = db.Column(db.Integer, db.ForeignKey('state.id'), nullable=True, index=True)
    country_id = db.Column(
        db.Integer, db.ForeignKey('country.id'), nullable=True, index=True)
    users = db.relationship('User', backref='university', lazy='dynamic')


class Banner(AppMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=False)
    alt_text = db.Column(db.String(200), unique=False)
    url = db.Column(db.String(200), unique=False)
    width = db.Column(db.Float)
    height = db.Column(db.Float)
    is_visible = db.Column(db.Boolean, default=True)

    @property
    def cover_image(self):
        return self


class Section(AppMixin, db.Model):
    __searchable__ = True

    __include_in_index__ = ["name", "cover_image_id", "slug", "description",
                            "position", "categories", "images", "cover_image", "cover_image_url"]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), index=True)
    cover_image_id = db.Column(db.Integer, index=True)
    slug = db.Column(db.String(200), unique=True, index=True)
    description = db.Column(db.String(200))
    position = db.Column(db.Integer, default=0, index=True)
    categories = db.relationship('Category', backref='dir_section',
                                 cascade="all,delete-orphan", lazy='dynamic', order_by='Category.position')
    images = db.relationship(
        'Image', backref='section', lazy='dynamic', cascade="all,delete-orphan")
    products = db.relationship(
        'Product', backref='section', lazy='dynamic')

    @property
    def cover_image(self):
        """ Retrieves the cover image from the list of images """
        if self.cover_image_id:
            return Image.query.get(self.cover_image_id)
        else:
            cover_image = self.images.filter().first()
            self.cover_image_id = cover_image.id

            # On first call, set the cover image id to prevent subsequent
            # searching
            try:
                db.session.add(self)
                db.session.commit()
            except:
                db.session.rollback()
                raise

            return cover_image

    @property
    def cover_image_url(self):
        """ Retrieves the cover image from the list of images """
        if self.cover_image:
            return self.cover_image.url
        else:
            return None


class Category(AppMixin, db.Model):
    __searchable__ = True

    __include_in_index__ = ["name", "slug", "section_id", "show_on_grocery",
                            "description", "position", "section", "filters", "tags"]

    __listeners_for_index__ = ["dir_section"]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    slug = db.Column(db.String(200), index=True)
    position = db.Column(db.Integer, default=0, index=True)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), index=True)
    description = db.Column(db.String(200))
    products = db.relationship(
        'Product', backref='category', lazy='dynamic')
    filters = db.relationship(
        'Filter', backref='category', lazy='dynamic', cascade="all, delete-orphan")
    tags = db.relationship(
        'CategoryTag', backref='category', lazy='dynamic')


class CategoryTag(AppMixin, db.Model):
    __searchable__ = True

    __include_in_index__ = ["name", "url", "slug", "description", "category_id", "is_redirect", "category",
                            "search_category_id", "section_id", "search_query", "tag_key", "app_exclusion_lists",
                            "search_category", "targeted_category"]

    __listeners_for_index__ = ["dir_category"]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=False, nullable=False)
    url = db.Column(db.String(200), unique=False, nullable=False, index=True)
    slug = db.Column(db.String(200), nullable=False,
                     default=slugify_from_name, index=True)
    description = db.Column(db.String(200))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), index=True)
    search_category_id = db.Column(db.Integer, index=True)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), index=True)
    search_query = db.Column(db.String(200), nullable=True)
    tag_key = db.Column(db.String(200), nullable=True)
    highlight = db.Column(db.String(200))
    is_redirect = db.Column(db.Boolean, default=False)


class ProductTag(AppMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=False)
    slug = db.Column(db.String(200), nullable=False,
                     default=slugify_from_name, onupdate=slugify_from_name, index=True)
    classification = db.Column(db.String(200))

    def __repr__(self):
        return '<ProductTag %r>' % self.name

    def __unicode__(self):
        return self.name


class ProductType(AppMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=False)
    slug = db.Column(db.String(200), nullable=False,
                     default=slugify_from_name, onupdate=slugify_from_name, index=True)
    products = db.relationship('Product', backref='product_type', lazy='dynamic')

    def __repr__(self):
        return '<ProductType %r>' % self.name


product_tags = db.Table('product_tags',
                        db.Column('product_tag_id', db.Integer,
                                  db.ForeignKey('product_tag.id')),
                        db.Column('product_id', db.Integer,
                                  db.ForeignKey('product.id'))
                        )


class Product(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), index=True)
    description = db.Column(db.Text, unique=False)
    title = db.Column(db.String(200), unique=False)
    caption = db.Column(db.Text, unique=False, default=0)
    track_stock_level = db.Column(db.Boolean, default=False)
    regular_price = db.Column(db.Float, unique=False, default=0)
    quantity = db.Column(db.Integer, unique=False)
    sale_price = db.Column(db.Float, default=0)
    sku = db.Column(db.String(200), unique=False)
    weight = db.Column(db.Float)
    require_shipping = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=True, index=True)
    visibility = db.Column(db.Boolean, default=False, index=True)
    images = db.relationship('Image', backref='product',
                             lazy='dynamic', cascade="all,delete-orphan")
    type_id = db.Column(db.Integer, db.ForeignKey('product_type.id'), index=True)
    cover_image_id = db.Column(db.Integer)  # over image among all images
    is_flexible = db.Column(db.Boolean, default=False)
    variants = db.relationship(
        'Variant', backref='product', lazy='dynamic', cascade="all,delete-orphan")
    options = db.relationship(
        'Option', backref='product', lazy='dynamic', cascade="all,delete-orphan")
    tags = db.relationship('ProductTag', secondary="product_tags",
                           backref=db.backref('products', lazy='dynamic'))
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), index=True)
    show_price = db.Column(db.Boolean, default=True)
    is_donation = db.Column(db.Boolean, default=False)
    is_private = db.Column(db.Boolean, default=False, index=True)
    is_quick_product = db.Column(db.Boolean, default=False, index=True)
    on_deal = db.Column(db.Boolean, default=False)
    deal_start = db.Column(db.DateTime)
    deal_end = db.Column(db.DateTime)
    view_count = db.Column(db.Integer)
    is_enabled = db.Column(db.Boolean, default=True, index=True)
    has_variants = db.Column(db.Boolean)

    @property
    def deal_end_timestamp(self):
        if self.on_deal and self.deal_end > self.deal_start:
            _full_day = self.deal_end + timedelta(days=1)
            return int(_full_day.strftime('%s')) * 1000
        else:
            return None


    @property
    def cover_image(self):
        """ Retrieves the cover image from the list of images """
        if self.cover_image_id:
            return Image.query.get(self.cover_image_id)
        else:
            cover_image = self.images.filter().first()
            if cover_image:
                self.cover_image_id = cover_image.id

            # On first call, set the cover image id to prevent subsequent
            # searching
            try:
                db.session.add(self)
                db.session.commit()
            except:
                db.session.rollback()
                raise

            return cover_image

    @property
    def cover_image_url(self):
        if self.cover_image:
            return self.cover_image.url
        else:
            return None


    @property
    def alternate_image(self):
        return Image.query.filter(Image.product_id == self.id, Image.id != self.cover_image.id).first()

    @property
    def alternate_image_url(self):
        image = Image.query.filter(
            Image.product_id == self.id, Image.id != self.cover_image.id).first()
        return image.url

    def untracked_variant(self):
        """ Returns the untracked variant of a product. This object holds the core values that affect a purchase """

        return Variant.query.filter(Variant.product == self, Variant.untracked == True).first()

    @property
    def price(self):
        if self.on_deal:
            price = self.sale_price
        else:
            price = self.regular_price

        return price

    @property
    def percentage_off(self):
        self_price = self.price
        if self.sale_price > 0.0 and self.sale_price < self.regular_price:
            """ Gets the discount price """
            dp = self.sale_price
            """ Gets the standard price """
            sp = self.regular_price

            """ Calculates the percentage off """
            po = int(((sp - dp) / sp) * 100)
            return po
        else:
            return False


    def __repr__(self):
        return '<Product %r>' % self.name



class Variant(AppMixin, db.Model):
    __listeners_for_index__ = ["product"]

    __sub_cubes__ = [{'transaction_entry': ['price'],
                      'measurables': [{'name': 'money_made', 'function': 'price*quantity', 'aggregations': ['sum']},
                                      {'name': 'units_sold', 'function': 'quantity', 'aggregations': ['sum']}]}]

    __simple_dimensions__ = [{'details': ['name']}]
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=False)
    visibility = db.Column(db.Boolean, default=False, index=True)
    quantity = db.Column(db.Integer)
    sku = db.Column(db.String(200), index=True)
    untracked = db.Column(db.Boolean, default=False)
    price = db.Column(db.Float, default=0)
    compare_at = db.Column(db.Float, default=0)
    options = db.Column(db.String(200))
    track_stock_level = db.Column(db.Boolean, default=True)
    product_id = db.Column(db.Integer, db.ForeignKey(
        'product.id'), nullable=False, index=True)
    is_flexible = db.Column(db.Boolean, default=False)

    @property
    def cart_price(self):
        _cart_price = self.compare_at or 0
        if self.compare_at > 0:
            _cart_price = self.compare_at
        else:
            _cart_price = self.price

        return _cart_price

    def __repr__(self):
        return '<Variant %r>' % self.name


class Option(AppMixin, db.Model):
    # Product Option
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=False)
    values = db.Column(db.String(200), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey(
        'product.id'), nullable=False, index=True)


class Filter(AppMixin, db.Model):
    __searchable__ = True

    __include_in_index__ = ["name", "options", "category"]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    options = db.relationship('FilterOption', backref='filter')
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), index=True)


class FilterOption(AppMixin, db.Model):
    __searchable__ = True

    __include_in_index__ = ["name", "slug", "values", "filter"]

    __listeners_for_index__ = ["filter"]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    slug = db.Column(db.String(200), index=True)
    values = db.Column(db.String(200), nullable=True)
    filter_id = db.Column(db.Integer, db.ForeignKey('filter.id'), index=True)


class BlogPost(AppMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=False)
    slug = db.Column(db.String(200), index=True)
    content = db.Column(db.Text, nullable=True)
    comments = db.relationship('BlogPostComment', backref='blog_post')
    likes = db.relationship('BlogPostLike', backref='blog_post')
    post_tags = db.relationship(
        'BlogPostTag', secondary="post_tags", backref=db.backref('blog_post', lazy='dynamic'))


class BlogPostComment(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blog_post_id = db.Column(
        db.Integer, db.ForeignKey('blog_post.id'), index=True)
    comment = db.Column(db.Text)


class BlogPostLike(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blog_post_id = db.Column(
        db.Integer, db.ForeignKey('blog_post.id'), index=True)


post_tags = db.Table('post_tags',
                     db.Column('blog_post_id', db.Integer,
                               db.ForeignKey('blog_post.id')),
                     db.Column('blog_post_tag_id', db.Integer,
                               db.ForeignKey('blog_post_tag.id'))
                     )


class BlogPostTag(AppMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, default=slugify_from_name, index=True)


class Coupon(AppMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=False)
    is_active = db.Column(db.Boolean, default=False, index=True)


class Wishlist(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    slug = db.Column(db.String(200), nullable=True)
    is_private = db.Column(db.Boolean, default=False)
    entries = db.relationship(
        'WishlistEntry', cascade="all,delete-orphan", backref='wishlist', lazy='dynamic')


class WishlistEntry(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey(
        'product.id'), nullable=False)
    wishlist_id = db.Column(db.Integer, db.ForeignKey(
        'wishlist.id'), nullable=False)

