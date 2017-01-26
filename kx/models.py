# Models

from kx import db, bcrypt, app, logger
from kx.core.utils import slugify, id_generator
from flask.ext.login import UserMixin
from sqlalchemy import or_
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method, Comparator
from sqlalchemy.inspection import inspect
from datetime import datetime
import hashlib
from sqlalchemy import func, asc, desc
from sqlalchemy import inspect, UniqueConstraint, desc
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.collections import InstrumentedList
from sqlalchemy.orm import dynamic
from flask import url_for
import inspect as pyinspect


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
    return hashlib.md5("%s:%s:%s" % (context.current_parameters["user_id"], context.current_parameters["email"], str(datetime.now()))).hexdigest()




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
                     if k in include_only + extras and isinstance(getattr(self, k), (db.Model, db.Query, InstrumentedList, dynamic.AppenderMixin)) is False
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
        return db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    @property
    def user(self):
        if self.user_id:
            return User.query.get(self.user_id)
        else:
            return None


class City(AppMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    code = db.Column(db.String(200))
    state_id = db.Column(db.Integer, db.ForeignKey('state.id'), nullable=False)
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'), nullable=False)


class State(AppMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    slug = db.Column(db.String(200), unique=True, default=slugify_from_name, onupdate=slugify_from_name)
    code = db.Column(db.String(200))
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'), nullable=False)
    cities = db.relationship('City', backref='state', lazy='dynamic')


class Country(AppMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    slug = db.Column(db.String(200), unique=True, default=slugify_from_name)
    code = db.Column(db.String(200))
    enabled = db.Column(db.Boolean, default=False)
    states = db.relationship('State', backref='country', lazy='dynamic')
    cities = db.relationship('City', backref='country', lazy='dynamic')


class Timezone(AppMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    code = db.Column(db.String(200))
    offset = db.Column(db.String(200))  # UTC time


class Currency(AppMixin, db.Model):

    __searchable__ = True

    __include_in_index__ = ["name", "code",
                            "enabled", "symbol", "payment_code"]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    code = db.Column(db.String(200))
    enabled = db.Column(db.Boolean, default=False)
    symbol = db.Column(db.String(200))
    payment_code = db.Column(db.String(200))

    def __unicode__(self):
        return "%s (%s)" % (self.name.title(), self.code)

    def __repr__(self):
        return '<Currency %r>' % self.name



class Image(AppMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=False)
    alt_text = db.Column(db.String(200), unique=False)
    url = db.Column(db.String(200), unique=False)
    width = db.Column(db.Float)
    height = db.Column(db.Float)
    product_id = db.Column(
        db.Integer, db.ForeignKey('product.id'), nullable=True)
    section_id = db.Column(
        db.Integer, db.ForeignKey('section.id'), nullable=True)
    banner_id = db.Column(
        db.Integer, db.ForeignKey('banner.id'), nullable=True)
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
    email = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.Text)
    url = db.Column(db.Text, nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    has_parent = db.Column(db.Boolean, default=False)
    user_read = db.Column(db.Boolean, default=False)
    is_replied = db.Column(db.Boolean, default=False)
    date_replied = db.Column(db.DateTime, nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    body = db.Column(db.Text)  # for plain text messages
    responses = db.relationship(
        'MessageResponse', backref='message', lazy='dynamic', cascade="all,delete-orphan")


class MessageResponse(AppMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(
        db.Integer, db.ForeignKey('message.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    body = db.Column(db.Text)  # for plain text messages


class AdminMessage(AppMixin, db.Model):

    __searchable__ = True

    __include_in_index__ = ["name", "email", "phone", "subject", "is_read", "has_parent",
                            "user_read", "is_replied", "date_replied", "body", "responses", "user_id"]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False)
    user_read = db.Column(db.Boolean, default=False)
    has_parent = db.Column(db.Boolean, default=False)
    is_replied = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    date_replied = db.Column(db.DateTime, nullable=True)
    body = db.Column(db.Text)  # for plain text messages
    responses = db.relationship(
        'AdminMessageResponse', backref='admin_message', lazy='dynamic', cascade="all,delete-orphan")


class AdminMessageResponse(AppMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_message_id = db.Column(db.Integer, db.ForeignKey(
        'admin_message.id'), nullable=False)
    body = db.Column(db.Text)  # for plain text messages
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)



class User(db.Model, UserMixin, AppMixin):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), unique=True)
    email = db.Column(db.String(200), unique=True)
    first_name = db.Column(db.String(200), unique=False)
    last_name = db.Column(db.String(200), unique=False)
    full_name = db.Column(db.String(200), unique=False)
    password = db.Column(db.Text, unique=False)
    active = db.Column(db.Boolean, default=False)
    is_confirmed = db.Column(db.Boolean, default=False)
    is_staff = db.Column(db.Boolean, default=False)
    is_global = db.Column(db.Boolean, default=False)
    is_super_admin = db.Column(db.Boolean, default=False)
    deactivate = db.Column(db.Boolean, default=False)
    gender = db.Column(db.String(200))
    location = db.Column(db.String(200))
    dob = db.Column(db.DateTime)
    login_count = db.Column(db.Integer, default=0)
    last_login_at = db.Column(db.DateTime)
    current_login_at = db.Column(db.DateTime)
    last_login_ip = db.Column(db.String(200))
    current_login_ip = db.Column(db.String(200))

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

    def add_role(self, role):
        """
        Adds a the specified role to the user
        :param role: Role ID or Role name or Role object to be added to the user

        """
        try:

            if isinstance(role, Role) and hasattr(role, "id"):
                role_obj = role
            elif type(role) is int:
                role_obj = Role.query.get(role)
            elif type(role) is str:
                role_obj = Role.query.filter(Role.name == role.lower()).one()

            if not role_obj:
                raise Exception("Specified role could not be found")

            if self.has_role(role_obj) is False:
                self.roles.append(role_obj)
                db.session.add(self)
                db.session.commit()
                return self
        except:
            db.session.rollback()
            raise

    def has_role(self, role):
        """
        Returns true if a user identifies with a specific role

        :param role: A role name or `Role` instance
        """
        return role in self.roles

    def add_access_group(self, access_group):
        """
        Adds a the specified access group to the user
        :param group: AccessGroup ID or AccessGroup name or AccessGroup object to be added to the user

        """
        try:

            if isinstance(access_group, AccessGroup) and hasattr(access_group, "id"):
                group_obj = access_group
            elif type(access_group) is int:
                group_obj = AccessGroup.query.get(access_group)
            elif type(access_group) is str:
                group_obj = AccessGroup.query.filter(
                    AccessGroup.name == access_group.lower()).one()

            if not group_obj:
                raise Exception("Specified access_group could not be found")

            if self.has_access_group(group_obj) is False:
                self.access_groups.append(group_obj)
                db.session.add(self)
                db.session.commit()
                return self
        except:
            db.session.rollback()
            raise

    def has_access_group(self, access_group):
        """
        Returns true if a user identifies with a specific access_group

        :param access_group: A access_group name or `AccessGroup` instance
        """
        return access_group in self.access_groups


class University(AppMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=False, nullable=False)
    handle = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text)
    about_information = db.Column(db.Text)  # information for your about page
    thumbnail = db.Column(db.Text)  # storefront thumbnail url
    logo = db.Column(db.Text)  # storefront thumbnail url
    city_id = db.Column(db.Integer, db.ForeignKey('city.id'), nullable=True)
    is_enabled = db.Column(db.Boolean, default=False)
    state_id = db.Column(db.Integer, db.ForeignKey('state.id'), nullable=True)
    country_id = db.Column(
        db.Integer, db.ForeignKey('country.id'), nullable=True)

    def add_user(self, username, email, password, full_name=None, is_staff=True, is_verified=True, is_admin=False, is_global=False, is_super_admin=False, active=False):
        """
        Adds a user to a university

        :param username: username (should be unique)
        :type username: string
        :param email: email address (should be unique)
        :type email: string
        :param password: user's password. (this is automatically encrypted)
        :type email: string
        :param full_name: user's full name (optional)
        :type full_name: string
        :param active

        :returns: a User object or None
        :rtype: dml.models.User

        """
        try:
            user = User(username=username, email=email,
                        full_name=full_name, active=active, is_staff=True, is_verified=True, is_mtn=False, is_global=False, is_super_admin=False)
            user.generate_password(password)
            self.users.append(user)
            db.session.commit()
            if is_admin:
                self.owner_id = user.id
                db.session.add(self)
                db.session.commit()
            return user
        except:
            db.session.rollback()
            raise


    @property
    def owner(self):
        if self.owner_id:
            return User.query.get(self.owner_id)
        else:
            return None

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
    name = db.Column(db.String(200))
    cover_image_id = db.Column(db.Integer)
    slug = db.Column(db.String(200), unique=True)
    description = db.Column(db.String(200))
    position = db.Column(db.Integer, default=0)
    categories = db.relationship('Category', backref='dir_section',
                                 cascade="all,delete-orphan", lazy='dynamic', order_by='Category.position')
    images = db.relationship(
        'Image', backref='section', lazy='dynamic', cascade="all,delete-orphan")
    products = db.relationship(
        'Product', backref='section', lazy='dynamic')
    sla_refund_period = db.Column(db.Integer, default=0)
    sla_type = db.Column(db.String(200), nullable=True)

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
    slug = db.Column(db.String(200))
    position = db.Column(db.Integer, default=0)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'))
    description = db.Column(db.String(200))
    products = db.relationship(
        'Product', backref='category', lazy='dynamic')
    filters = db.relationship(
        'Filter', backref='category', lazy='dynamic', cascade="all, delete-orphan")
    tags = db.relationship(
        'CategoryTag', backref='category', lazy='dynamic')


class CategoryTag(AppMixin, db.Model):
    __searchable__ = True

    __include_in_index__ = ["name", "url", "slug","description", "category_id", "is_redirect", "category", "search_category_id", "section_id", "search_query", "tag_key", "app_exclusion_lists", "search_category", "targeted_category"]

    __listeners_for_index__ = ["dir_category"]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=False, nullable=False)
    url = db.Column(db.String(200), unique=False, nullable=False)
    slug = db.Column(db.String(200), nullable=False,
                     default=slugify_from_name)
    description = db.Column(db.String(200))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    search_category_id = db.Column(db.Integer)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'))
    search_query = db.Column(db.String(200), nullable=True)
    tag_key = db.Column(db.String(200), nullable=True)
    highlight = db.Column(db.String(200))
    is_redirect = db.Column(db.Boolean, default=False)

    @property
    def search_category(self):
        if self.search_category_id:
            return DirCategory.query.get(self.search_category_id)
        else:
            return None

    @property
    def targeted_category(self):
        if self.search_category:
            return self.search_category
        else:
            return DirCategory.query.get(self.category_id)


class Tag(AppMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=False)
    slug = db.Column(db.String(200), nullable=False,
                     default=slugify_from_name, onupdate=slugify_from_name)
    classification = db.Column(db.String(200))

    def __repr__(self):
        return '<Tag %r>' % self.name

    def __unicode__(self):
        return self.name


class ProductType(AppMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=False)
    slug = db.Column(db.String(200), nullable=False,
                     default=slugify_from_name, onupdate=slugify_from_name)
    products = db.relationship('Product', backref='product_type', lazy='dynamic')

    def __repr__(self):
        return '<ProductType %r>' % self.name


product_tags = db.Table('product_tags',
    db.Column('tag_id', db.Integer,
              db.ForeignKey('tag.id')),
    db.Column('product_id', db.Integer,
              db.ForeignKey('product.id'))
    )


class Product(AppMixin, db.Model):

    __searchable__ = True

    __include_in_index__ = ["name", "raw_name", "currency", "description", "title", "sku", "show_price", "is_donation", "is_private", "product_type",
                            "variants", "group", "section", "category", "cart_price", "price", "compare_at", "url",
                            "cover_image_url", "alternate_image_url", "percentage_off", "track_stock_level", "is_featured", "visibility", "images", "is_flexible",
                            "product_customs", "cart_choices", "handle", "quantity", "is_quick_product", "deal_end_timestamp", "on_deal", "deal_start",
                             "deal_end"]

    __listeners_for_index__ = ["user"]

    __sub_cubes__ = [{'variant': ['name']}, {'option': ['name']}]

    __simple_dimensions__ = [{'desc': ['name', 'title']}]

    # __ngram_fields__ = ["name", "title", "caption", "description"]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=False)
    description = db.Column(db.Text, unique=False)
    title = db.Column(db.String(200), unique=False)
    caption = db.Column(db.Text, unique=False, default=0)
    track_stock_level = db.Column(db.Boolean, default=False)
    _price = db.Column(db.Float, unique=False, default=0)
    _quantity = db.Column(db.Integer, unique=False)
    _compare_at = db.Column(db.Float, default=0)
    sku = db.Column(db.String(200), unique=False)
    weight = db.Column(db.Float)
    require_shipping = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=True)
    visibility = db.Column(db.Boolean, default=False)
    images = db.relationship('Image', backref='product',
                             lazy='dynamic', cascade="all,delete-orphan")
    type_id = db.Column(db.Integer, db.ForeignKey('product_type.id'))
    cover_image_id = db.Column(db.Integer)  # over image among all images
    is_flexible = db.Column(db.Boolean, default=False)
    variants = db.relationship(
        'Variant', backref='product', lazy='dynamic', cascade="all,delete-orphan")
    options = db.relationship(
        'Option', backref='product', lazy='dynamic', cascade="all,delete-orphan")
    tags = db.relationship('Tag', secondary="product_tags",
                           backref=db.backref('products', lazy='dynamic'))
    section_id = db.Column(db.Integer, db.ForeignKey(
        'section.id', ondelete='SET NULL'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey(
        'category.id', ondelete='SET NULL'), nullable=True)
    show_price = db.Column(db.Boolean, default=True)
    is_donation = db.Column(db.Boolean, default=False)
    is_private = db.Column(db.Boolean, default=False)
    is_quick_product = db.Column(db.Boolean, default=False)
    on_deal = db.Column(db.Boolean, default=False)
    deal_start = db.Column(db.DateTime)
    deal_end = db.Column(db.DateTime)
    view_count = db.Column(db.Integer)

    @property
    def deal_end_timestamp(self):
        if self.on_deal and self.deal_end > self.deal_start:
            _full_day = self.deal_end + timedelta(days=1)
            return int(_full_day.strftime('%s')) * 1000
        else:
            return None

    @property
    def raw_name(self):
        return self.name


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

    @hybrid_property
    def quantity(self):
        """ Hybrid property to return the total variant's count based """
        if self.track_stock_level is False:
            variant = self.untracked_variant()
            if variant:
                return variant.quantity
        else:
            # first build the base query to filter by
            return db.session.query(func.sum(Variant.quantity)).filter(Variant.product == self, Variant.untracked == False).scalar()

    @quantity.setter
    def quantity(self, value):
        """ the setter for quantity """
        self._quantity = value

    @hybrid_property
    def price(self):
        if self.track_stock_level is False:
            if self.product_type == "Product":
                variant = Variant.query.filter(
                    Variant.product == self, Variant.untracked == True).first()
                if not variant:
                    return self._price
                else:
                    return variant.price
            else:
                return self._price
        else:
            return self._price

    @property
    def cart_price(self):
        _cart_price = self.compare_at or 0
        if self.compare_at > 0:
            _cart_price = self.compare_at
        else:
            _cart_price = self.price

        return _cart_price

    @price.setter
    def price(self, value):
        """ the setter for quantity """
        self._price = value

    @hybrid_property
    def compare_at(self):
        if self.track_stock_level is False:
            variant = Variant.query.filter(
                Variant.product == self, Variant.untracked == True).first()
            if not variant:
                return self._compare_at
            else:
                return variant.compare_at
        else:
            return self._compare_at

    @property
    def percentage_off(self):
        if self._compare_at > 0.0 and self.price > 0 and self._compare_at < self._price:
            """ Gets the discount price """
            dp = self.cart_price
            """ Gets the standard price """
            sp = self.price

            """ Calculates the percentage off """
            po = int(((sp - dp) / sp) * 100)
            return str(po) + "%"
        else:
            return False

    @compare_at.setter
    def compare_at(self, value):
        """ the setter for quantity """
        self._compare_at = value

    @property
    def handle(self):
        return slugify(self.name)

    def __repr__(self):
        return '<Product %r>' % self.name

    @property
    def avg_rating(self):
        if self.reviews.count() > 0:
            ratings = [r.rating for r in self.reviews if r.rating != None]
            avg = sum(ratings) / self.reviews.count()

            return avg
        else:
            return 0.0

    # @property
    # def url(self):
    #     return "%s%s.%s/%ss/%s/%s/" % (app.config.get("PROTOCOL"), self.shop.handle, app.config.get("DOMAIN"), self.product_type.lower(), self.id, slugify(self.name))

    @property
    def cover_image_url(self):
        if self.cover_image:
            return self.cover_image.url
        else:
            return None

    # @property
    # def directory_url(self):
    #     return url_for('.itempage', handle=self.shop.handle, id=self.id)
    #

class Variant(AppMixin, db.Model):

    __listeners_for_index__ = ["product"]

    __sub_cubes__ = [{'transaction_entry': ['price'], 'measurables': [{'name': 'money_made', 'function': 'price*quantity', 'aggregations': ['sum']},
                                                                      {'name': 'units_sold', 'function': 'quantity', 'aggregations': ['sum']}]}]

    __simple_dimensions__ = [{'details': ['name']}]
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=False)
    visibility = db.Column(db.Boolean, default=False)
    quantity = db.Column(db.Integer)
    sku = db.Column(db.String(200))
    untracked = db.Column(db.Boolean, default=False)
    price = db.Column(db.Float, default=0)
    compare_at = db.Column(db.Float, default=0)
    options = db.Column(db.String(200))
    track_stock_level = db.Column(db.Boolean, default=True)
    product_id = db.Column(db.Integer, db.ForeignKey(
        'product.id'), nullable=False)
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
        'product.id'), nullable=False)


class SessionCart(AppMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=True)
    total = db.Column(db.Float, default=0.0)
    phone = db.Column(db.String(200), nullable=True)
    email = db.Column(db.String(200), nullable=True)
    address_line1 = db.Column(db.String(200), nullable=True)
    address_line2 = db.Column(db.String(200), nullable=True)
    city = db.Column(db.String(200), nullable=True)
    state_id = db.Column(db.Integer, db.ForeignKey('state.id'), nullable=True)
    country_id = db.Column(
        db.Integer, db.ForeignKey('country.id'), nullable=True)
    payment_option_id = db.Column(
        db.Integer, db.ForeignKey('payment_option.id'), nullable=True)
    delivery_option_id = db.Column(
        db.Integer, db.ForeignKey('delivery_option.id'), nullable=True)
    cart_items = db.relationship(
        'SessionCartItem', cascade="all,delete-orphan", backref='session_cart', lazy='dynamic')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    auto_set_shipment = db.Column(db.Boolean, default=False)
    shipment_name = db.Column(db.String(200), nullable=True)
    shipment_phone = db.Column(db.String(200), nullable=True)
    shipment_address = db.Column(db.String(300), nullable=True)
    shipment_city = db.Column(db.String(200))
    shipment_description = db.Column(db.String(200))
    shipment_state = db.Column(db.String(200), nullable=True)
    shipment_country = db.Column(db.String(200), nullable=True)
    is_gtb_cust = db.Column(db.Boolean, default=False)
    unconfirmed = db.Column(db.Boolean, default=False)

    # @property
    # def delivery_charge(self):
    #     s_state = State.query.filter(State.name == self.shipment_state).first()
    #     if s_state:
    #         _charge = self.shop.fetch_delivery_charge(s_state.id) or 0.0
    #     else:
    #         return 0.0
    #
    #     if self.delivery_option and self.delivery_option.handle == "customer_pickup":
    #         return 0.0
    #     else:
    #         types = []
    #         p = "Product"
    #         for i in self.cart_items:
    #             types.append(i.variant.product.product_type)
    #         if p in types:
    #             return _charge
    #         else:
    #             return 0.0

    def add_item(self, variant_id, quantity, replace=False, **kwargs):
        """ Append a session cart item to the cart """

        cart_item = SessionCartItem.query.filter(
            SessionCartItem.session_cart == self, SessionCartItem.variant_id == variant_id).first()
        if cart_item:
            if replace:
                cart_item.quantity = quantity
            else:
                cart_item.quantity += quantity
        else:
            cart_item = SessionCartItem(session_cart=self, variant_id=variant_id, quantity=quantity)

        db.session.add(cart_item)
        db.session.commit()
        logger.info("Item Successfully added to SessionCartItem")

        for key, value in kwargs.items():

            if isinstance(value, (str, unicode)):
                logger.info("Instance check to validate extra value")

                extra = SessionCartItemExtra(
                    session_cart_item_id=cart_item.id)
                extra.name = key.upper().replace("_", " ")
                extra.value = value

                db.session.add(extra)
                db.session.commit()
                logger.info(
                    "Extra Info. Successfully added to SessionCartItem")

        return cart_item

    def add_donation_item(self, variant_id, **kwargs):
        """ Append a session cart item to the cart """
        price = kwargs["price"]
        cart_item = SessionCartItem.query.filter(
            SessionCartItem.session_cart_id == self.id, SessionCartItem.variant_id == variant_id).first()

        if cart_item:
            cart_item._price = price
            cart_item.price = price
        else:
            cart_item = SessionCartItem(session_cart_id=self.id,
                                        quantity=1, _price=price, price=price, variant_id=variant_id, is_flexible=True)

        db.session.add(cart_item)
        db.session.commit()
        logger.info("Item Successfully added to SessionCartItem")

        kwargs.pop("price", [])

        for key, value in kwargs.items():
            if isinstance(value, (str, unicode, list)):
                logger.info("Instance check to validate extra value")
                extra = SessionCartItemExtra(
                    session_cart_item_id=cart_item.id)
                extra.name = key.upper().replace("_", " ")
                extra.value = value

                db.session.add(extra)
                db.session.commit()
                logger.info(
                    "Extra Info. Successfully added to SessionCartItem")
        return cart_item

    def items(self):
        return SessionCartItem.query.filter(SessionCartItem.session_cart == self).order_by(asc(SessionCartItem.variant_id)).all()

    @property
    def cart_total(self):
        return sum([c.total for c in self.cart_items.filter().all()])

    @property
    def total(self):
        return self.delivery_charge + sum([c.total for c in self.cart_items.filter().all()])

    @property
    def total_quantity(self):
        return sum([c.quantity for c in self.cart_items.filter().all()])


class SessionCartItem(AppMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_cart_id = db.Column(db.Integer, db.ForeignKey(
        'session_cart.id'), nullable=False)
    variant_id = db.Column(
        db.Integer, db.ForeignKey('variant.id'), nullable=True)
    quantity = db.Column(db.Integer, default=0)
    is_flexible = db.Column(db.Boolean, default=False)
    _price = db.Column(db.Float, default=0.0)

    @hybrid_property
    def price(self):
        if self.is_flexible:
            return self._price
        else:
            return self.variant.cart_price

    @property
    def product_type(self):
        return self.variant.product.product_type

    @price.setter
    def price(self, value):
        """ the setter for quantity """
        self._price = value

    @hybrid_property
    def total(self):
        """Calculates the total charge of this item """
        return self.quantity * self.price

    def __repr__(self):
        return '<Session Cart Item %r>' % self.variant.id



class Order(AppMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    discount = db.Column(db.Float, default=0.0)
    delivery_charge = db.Column(db.Float, default=0.0)
    code = db.Column(db.String(200), nullable=False)
    coupon_code = db.Column(db.String(200), nullable=True)
    message = db.Column(db.Text, nullable=True)
    cart_name = db.Column(db.String(200), nullable=True)
    # considering either verified or not
    verified_status = db.Column(db.Boolean, default=False)
    payment_option_id = db.Column(db.Integer, db.ForeignKey(
        'payment_option.id'), nullable=False)
    payment_status_id = db.Column(
        db.Integer, db.ForeignKey('payment_status.id'), nullable=True)
    delivery_option_id = db.Column(
        db.Integer, db.ForeignKey('delivery_option.id'), nullable=True)
    delivery_status_id = db.Column(
        db.Integer, db.ForeignKey('delivery_status.id'), nullable=True)
    order_status_id = db.Column(
        db.Integer, db.ForeignKey('order_status.id'), nullable=True)
    # Adding address information to the order
    email = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(200), nullable=False)
    address_line1 = db.Column(db.String(200), nullable=False)
    address_line2 = db.Column(db.String(200), nullable=True)
    city = db.Column(db.String(200), nullable=False)
    state_id = db.Column(db.Integer, db.ForeignKey('state.id'), nullable=False)
    country_id = db.Column(db.Integer, db.ForeignKey(
        'country.id'), nullable=False)
    auto_set_shipment = db.Column(db.Boolean, default=False)
    shipment_name = db.Column(db.String(200), nullable=True)
    shipment_phone = db.Column(db.String(200), nullable=True)
    shipment_address = db.Column(db.String(300), nullable=True)
    shipment_city = db.Column(db.String(200))
    shipment_description = db.Column(db.String(200))
    shipment_state = db.Column(db.String(200), nullable=True)
    shipment_country = db.Column(db.String(200), nullable=True)
    is_gtb_cust = db.Column(db.Boolean, default=False)
    cust_contacted = db.Column(db.Boolean, default=False)
    owner_contacted = db.Column(db.Boolean, default=False)
    agent_comment = db.Column(db.Text, nullable=True)
    delivery_agent_id = db.Column(db.Integer, nullable=True)
    extimated_delivery_date = db.Column(db.DateTime, nullable=True)
    refund_requested = db.Column(db.Boolean, default=False)


    @property
    def name(self):
        if self.cart_name:
            return self.cart_name

    @property
    def delivery_agent(self):
        if self.delivery_agent_id:
            return DeliveryAgent.query.get(self.delivery_agent_id)
        else:
            return None

    @property
    def total(self):
        return self.delivery_charge + self.sub_total

    @property
    def etop_order_code(self):
        return self.date_created.strftime("%m%d%y") + str(self.id)

    @property
    def sub_total(self):
        return sum([c.total for c in self.entries.all()])

    @property
    def total_quantity(self):
        return sum([c.quantity for c in self.entries.all() if c and c.quantity is not None])

    @property
    def order_address(self):
        return "%s%s %s, %s %s" % (self.address_line1, " " + self.address_line2 or "", self.city, self.state.name, self.country.name)


class PaymentOption(AppMixin, db.Model):

    __searchable__ = True

    __include_in_index__ = ["name", "handle",
                            "description", "order", "is_enabled"]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    handle = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=True)
    session_carts = db.relationship(
        'SessionCart', backref="payment_option", lazy='dynamic', cascade="all,delete-orphan")
    orders = db.relationship('Order', backref="payment_option", lazy='dynamic')
    is_enabled = db.Column(db.Boolean, default=True)

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return '<PaymentOption %r>' % self.name



class DeliveryOption(AppMixin, db.Model):

    __searchable__ = True

    __include_in_index__ = ["name", "handle",
                            "description", "order", "session_cart"]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    handle = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=True)
    session_carts = db.relationship(
        'SessionCart', backref="delivery_option", lazy='dynamic', cascade="all,delete-orphan")
    orders = db.relationship(
        'Order', backref="delivery_option", lazy='dynamic')

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return '<DeliveryOption %r>' % self.name



class OrderStatus(AppMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    code = db.Column(db.String(200), nullable=False, unique=True)
    orders = db.relationship(
        "Order", cascade="all,delete-orphan", backref="order_status", lazy="dynamic")
    # order_entries = db.relationship(
    #     "OrderEntry", cascade="all,delete-orphan", backref="order_status", lazy="dynamic")


class PaymentStatus(AppMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    code = db.Column(db.String(200), nullable=False, unique=True)
    orders = db.relationship(
        "Order", cascade="all,delete-orphan", backref="payment_status", lazy="dynamic")
    # order_entries = db.relationship("Order", cascade="all,delete-orphan", backref="payment_status", lazy="dynamic")


class DeliveryStatus(AppMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    code = db.Column(db.String(200), nullable=False, unique=True)
    orders = db.relationship(
        "Order", cascade="all,delete-orphan", backref="delivery_status", lazy="dynamic")
    # order_entries = db.relationship("Order", cascade="all,delete-orphan", backref="delivery_status", lazy="dynamic")




class Filter(AppMixin, db.Model):

    __searchable__ = True

    __include_in_index__ = ["name", "options", "category"]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    options = db.relationship('FilterOption', backref='filter')
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))


class FilterOption(AppMixin, db.Model):

    __searchable__ = True

    __include_in_index__ = ["name", "slug", "values", "filter"]

    __listeners_for_index__ = ["filter"]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200))
    values = db.Column(db.String(200), nullable=True)
    filter_id = db.Column(db.Integer, db.ForeignKey('filter.id'))
