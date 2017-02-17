__author__ = 'kunsam002'

"""
restful.py

@Author: Ogunmokun Olukunle

"""

from kx.models import *
from sqlalchemy import asc, desc, or_, and_, func

def fetch_universities():
    return University.query.filter(University.is_enabled==True).order_by(University.name).all()

def fetch_top_view_products():
    return Product.query.order_by(desc(Product.view_count)).limit(12).all()

def fetch_states():
    return State.query.order_by(asc(State.name)).all()
