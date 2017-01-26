__author__ = 'kunsam002'

"""
restful.py

@Author: Ogunmokun Olukunle

"""
from kx import logger
from kx.models import *
from sqlalchemy import or_, and_
from kx.services import ServiceFactory

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

        obj = BaseUserService.create(ignored_args=ignored_args, **kwargs)
        logger.info(obj)
        obj = generate_password(obj.id, p)
        return obj
