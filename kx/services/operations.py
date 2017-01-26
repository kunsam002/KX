__author__ = 'kunsam002'

"""
restful.py

@Author: Ogunmokun Olukunle

"""

from kx.models import *
from sqlalchemy import or_, and_
from kx.services import ServiceFactory

SessionCartService = ServiceFactory.create_service(SessionCart, db)
SessionCartItemService = ServiceFactory.create_service(SessionCartItem, db)
OrderService = ServiceFactory.create_service(Order, db)
