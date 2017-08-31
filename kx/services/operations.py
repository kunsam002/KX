__author__ = 'kunsam002'

"""
restful.py

@Author: Ogunmokun Olukunle

"""

from kx import logger
from kx.models import *
from sqlalchemy import or_, and_
from kx.services import ServiceFactory
import itertools, os
from cloudinary.uploader import upload
import itertools
from flask_restful import abort
import cloudinary
from pprint import pprint
from kx.core import utils

ignored_args = ['id', 'date_created', 'last_updated', 'csrf_token']  # these attributes will be ignored

cloudinary.config(
    cloud_name='kampusxchange',
    api_key='791467912822196',
    api_secret='R0fI6eyqVWoRlQEs2pSzXeVVeCQ'
)

WishlistService = ServiceFactory.create_service(Wishlist, db)
WishlistEntryService = ServiceFactory.create_service(WishlistEntry, db)
ProductService = ServiceFactory.create_service(Product, db)
BaseImageService = ServiceFactory.create_service(Image, db)
BaseProductService = ServiceFactory.create_service(Product, db)
BaseVariantService = ServiceFactory.create_service(Variant, db)
MessageService = ServiceFactory.create_service(Message, db)
AdminMessageService = ServiceFactory.create_service(AdminMessage, db)

class ProductService(BaseProductService):
    """ Service class to handle product creation """

    @classmethod
    def create(cls, ignored_args=None, **kwargs):
        """ Custom create method support """
        images = kwargs.pop('image_ids', [])
        # variants = kwargs.pop('variants', [])
        # attributes = kwargs.pop('attributes', [])
        # product_details = kwargs.pop('product_details', [])
        # has_variants = kwargs.pop('has_variants', False)
        print kwargs, '====kwargs 1====='

        print kwargs, '========im the kwargs======'
        user = User.query.get(kwargs.get("user_id"))
        university = user.university
        section_id = kwargs.get("section_id", None)
        if section_id and section_id > 0 and Section.query.get(section_id).name == "Services":
            product_type = ProductType.query.filter(ProductType.slug == "service").first()
        else:
            product_type = ProductType.query.filter(ProductType.slug == "product").first()
        kwargs["product_type_id"] = product_type.id
        obj = BaseProductService.create(ignored_args=ignored_args, **kwargs)
        new_sku = "%s%s%s" % (
        university.handle[:3].upper(), utils.generate_numeric_code(obj.id, length=6), university.state.code)
        pprint(new_sku)
        new_kwargs = {"sku": new_sku}
        obj = cls.update(obj.id, **new_kwargs)

        kwargs['product_id'] = obj.id
        # ProductDescriptionService.create(product_details=product_details)

        # for image in images:
        #     pic = ImageService.update(image, product_id=obj.id)
        #
        # kwargs.pop('name')
        # kwargs.pop('regular_price')
        # kwargs.pop('sku')
        print "----------moving to gen variants"
        var_obj = cls.generate_variants(obj.id, **kwargs)

        # obj = BaseProductService.create(ignored_args=ignored_args, **kwargs)
        # kwargs['product_id'] = obj.id
        # ProductDescriptionService.create(product_details=product_details)

        # for image in images:
        #     pic = ImageService.update(image, product_id=obj.id)

        # obj = VariantService.create(obj.id, **kwargs)
        # channel = Channel.query.filter(Channel.business_id == kwargs.get('business_id'),
        #                                Channel.channel_type_code == "storefront").first()
        # to_store = kwargs.get('to_store', None)
        # print to_store, '=====to store======'

        return obj

    #
    # @classmethod
    # def update(cls, obj_id, **kwargs):
    #     image_ids = kwargs.pop('image_ids', [])
    #     variants = kwargs.pop('variants', [])
    #     attributes = kwargs.pop('attributes', [])
    #     product_details = kwargs.pop('product_details', [])
    #
    #     kwargs['variant_attributes'] = attributes
    #     product = cls.update(obj_id, **kwargs)
    #
    #     for item in variants:
    #         item_id = item.pop('id')
    #         variant = VariantService.update(item_id, **item)
    #
    #     for item in product_details:
    #         item_id = item.pop('id')
    #         detail = ProductDescriptionService.update(item_id, **item)
    #
    #     for id in image_ids:
    #         pic = ImageService.update(id, product_id=product.id)
    #
    #     return product

    # @classmethod
    # def set_cover_image(cls, obj_id, **kwargs):
    #     obj = cls.get(obj_id)
    #     cover = obj.cover_image
    #
    #     if cover:
    #         cover.is_cover = False
    #         ImageService.update(cover.id)
    #
    #     image_id = kwargs.get('image_id')
    #     ImageService.update(image_id, is_cover=True)

    @classmethod
    def get_attributes(cls, variant_attributes):
        """ Get product attributes from input as string and parse
        it into a dictionary"""

        string = variant_attributes
        d = string.split('|')
        print d
        e = [i.split(':') for i in d]
        attributes = []
        values = []
        for i in e:
            key = i[0].strip()
            v = i[1]
            value = v.split(',')
            value = [v.strip() for v in value]
            print value, 'value====='
            attributes.append(key)
            values.append(value)
        print [attributes, values]
        return [attributes, values]

    @classmethod
    def generate_variants(cls, obj_id, **kwargs):
        """ Spool all possible product variants from product attributes """
        kwargs['product_id'] = obj_id
        obj = cls.get(obj_id)
        if not obj.has_variants:
            variant = VariantService.create(**kwargs)
            return [variant]

        variant_attributes = obj.variant_attributes
        t = cls.get_attributes(variant_attributes)
        print t
        keys = '|'.join(t[0])
        print keys
        values = t[1]
        variant_list = []
        variants = itertools.product(*values)
        kwargs.pop('name', None)
        for i in variants:
            name = ' '.join(i)
            name = obj.name + ' ' + name
            kwargs.pop('regular_price', 0.0)
            kwargs.pop('quantity', 0)
            variant = VariantService.create(name=name, attribute_keys=keys,
                                            regular_price=obj.regular_price, **kwargs)
            variant_list.append(variant)
        return variant_list

    @classmethod
    def set_cover_image(cls, obj_id, **kwargs):
        obj = cls.update(obj_id, **kwargs)
        return obj


class VariantService(BaseVariantService):
    @classmethod
    def create(cls, ignored_args=None, **kwargs):
        obj = BaseVariantService.create(**kwargs)
        return obj

    @classmethod
    def add(cls, obj_id, **kwargs):
        variant = VariantService.get(obj_id)
        if variant:
            variant.quantity += kwargs.get('quantity')
            quantity = variant.quantity
            print quantity
            variant = VariantService.update(obj_id, quantity=quantity)

        return variant

    @classmethod
    def set(cls, obj_id, **kwargs):
        variant = VariantService.update(obj_id, quantity=kwargs.get('quantity'))
        return variant


class ImageService(BaseImageService):
    @classmethod
    def create(cls, ignored_args=None, **kwargs):
        # print(kwargs)
        if kwargs.get("path") is None:
            raise Exception('You have to upload at least one image')

        image = kwargs.get("path")
        upload_result = upload(image, public_id="KX" + str(datetime.today()))
        os.remove(image)
        kwargs["url"] = upload_result["url"]
        obj = BaseImageService.create(**kwargs)

        return obj
