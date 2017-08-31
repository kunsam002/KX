__author__ = 'kunsam002'

"""
restful.py

@Author: Ogunmokun Olukunle

"""
from kx import logger
from kx.models import *
from sqlalchemy import or_, and_
from kx.services import ServiceFactory
from kx.services.operations import WishlistService, WishlistEntryService, ProductService

BaseUserService = ServiceFactory.create_service(User, db)


def generate_password(obj_id, password):
    """
    Generates a password from the plain string

    :param password: plain password string
    """
    obj = User.query.get(obj_id)
    obj.password = bcrypt.generate_password_hash(password)
    db.session.add(obj)
    db.session.commit()


class UserService(BaseUserService):
    @classmethod
    def create(cls, ignored_args=None, **kwargs):

        p = kwargs.pop("password")
        logger.info(p)
        full_name = kwargs.get("full_name", "")
        full_name_split = full_name.split(" ")
        if len(full_name_split) > 1:
            kwargs["first_name"], kwargs["last_name"] = full_name.split(" ")
        else:
            kwargs["first_name"] = full_name
        obj = BaseUserService.create(ignored_args=ignored_args, **kwargs)
        obj = generate_password(obj.id, p)
        data = {"name": "General"}
        cls.create_wishlist(obj.id, **data)
        return

    @classmethod
    def reset_password(cls, obj_id, **kwargs):
        obj = cls.update(obj_id)
        p = kwargs.get("password", "")
        data = {"password": bcrypt.generate_password_hash(p)}
        obj = cls.update(obj.id, **data)
        return obj

    @classmethod
    def create_wishlist(cls, obj_id, **kwargs):
        obj = cls.update(obj_id)
        kwargs["user_id"] = obj.id
        wishlist = WishlistService.create(**kwargs)
        return wishlist

    @classmethod
    def create_product(cls, obj_id, **kwargs):
        obj = cls.update(obj_id)
        kwargs["user_id"] = obj.id
        product = ProductService.create(**kwargs)
        return product
