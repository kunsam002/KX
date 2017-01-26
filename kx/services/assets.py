__author__ = 'kunsam002'

"""
restful.py

@Author: Ogunmokun Olukunle

"""

from kx.models import *
from sqlalchemy import or_, and_
from kx.services import ServiceFactory

CityService = ServiceFactory.create_service(City, db)
StateService = ServiceFactory.create_service(State, db)
CountryService = ServiceFactory.create_service(Country, db)
TimezoneService = ServiceFactory.create_service(Timezone, db)
CurrencyService = ServiceFactory.create_service(Currency, db)
MessageService = ServiceFactory.create_service(Message, db)
MessageResponseService = ServiceFactory.create_service(MessageResponse, db)
AdminMessageService = ServiceFactory.create_service(AdminMessage, db)
AdminMessageResponseService = ServiceFactory.create_service(AdminMessageResponse, db)
UniversityService = ServiceFactory.create_service(University, db)
AdminBannerService = ServiceFactory.create_service(AdminBanner, db)
SectionService = ServiceFactory.create_service(Section, db)
CategoryService = ServiceFactory.create_service(Category, db)
CategoryTagService = ServiceFactory.create_service(CategoryTag, db)
TagService = ServiceFactory.create_service(Tag, db)
ProductTypeService = ServiceFactory.create_service(ProductType, db)
ProductService = ServiceFactory.create_service(Product, db)
VariantService = ServiceFactory.create_service(Variant, db)
OptionService = ServiceFactory.create_service(Option, db)
PaymentOptionService = ServiceFactory.create_service(PaymentOption, db)
DeliveryOptionService = ServiceFactory.create_service(DeliveryOption, db)
OrderStatusService = ServiceFactory.create_service(OrderStatus, db)
PaymentStatusService = ServiceFactory.create_service(PaymentStatus, db)
DeliveryStatusService = ServiceFactory.create_service(DeliveryStatus, db)
FilterService = ServiceFactory.create_service(Filter, db)
FilterOptionService = ServiceFactory.create_service(FilterOption, db)
