from kx.resources import BaseResource, ModelListField, ModelField
from kx.services.users import *
from kx.forms import *
from kx import register_api
from flask_restful import fields
from kx import logger


class UserResource(BaseResource):
    resource_name = 'users'
    service_class = UserService
    validation_form = SignupForm
    resource_fields = {
        "username": fields.String,
        "full_name": fields.String
    }



register_api(UserResource, '/users/', '/users/<int:id>/', '/users/<string>/')
