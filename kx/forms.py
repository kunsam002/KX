__author__ = 'kunsam002'

from flask_wtf import Form
from wtforms import Field, TextField, PasswordField, StringField, FieldList, FormField, \
    DateTimeField, DateField, BooleanField, DecimalField, validators, HiddenField, FloatField, \
    IntegerField, TextAreaField, SelectField, RadioField, SelectMultipleField, FileField
from wtforms.validators import DataRequired, Optional, Email, EqualTo, ValidationError
from datetime import datetime, date
from flask_wtf.html5 import EmailField
from wtforms import widgets
from wtfrecaptcha.fields import RecaptchaField
from kx import app, logger

class StringListField(Field):
	""" Custom field to support sending in multiple strings separated by commas and returning the content as a list """

	widget = widgets.TextInput()

	def __init__(self, label='', validators=None, **kwargs):
		super(StringListField, self).__init__(label, validators, **kwargs)

	def _value(self):
		if self.data:
			return u','.join(self.data)
		else:
			return u''

	def process_formdata(self, valuelist):
		if valuelist:
			self.data = [x.strip() for x in valuelist[0].split(',')]
		else:
			self.data = []

	def process_data(self, valuelist):
		if valuelist:
			self.data = [x.strip() for x in valuelist[0].split(',')]
		else:
			self.data = []


class IntegerListField(Field):
	""" Custom field to support sending in multiple integers separated by commas and returning the content as a list """

	widget = widgets.TextInput()

	def __init__(self, label='', validators=None, **kwargs):
		super(IntegerListField, self).__init__(label, validators, **kwargs)

	def _value(self):
		if self.data:
			string_data = [str(y) for y in self.data]
			return u','.join(string_data)
		else:
			return u''

	def process_formdata(self, valuelist):
		if valuelist:
			self.data = [int(x.strip()) for x in valuelist[0].split(',')]
		else:
			self.data = []

	def process_data(self, valuelist):
		if valuelist:
			self.data = [int(x.strip()) for x in valuelist[0].split(',')]
		else:
			self.data = []


class LoginForm(Form):
    username = StringField('Username or Email Address', validators=[DataRequired()],
                           description="Please enter a registered username or email")
    password = PasswordField('Password', validators=[DataRequired()], description="Please enter your valid password")


class SignupForm(Form):
    # username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    full_name = StringField('Full Name', validators=[DataRequired()])
    # first_name = StringField('First Name', validators=[DataRequired()])
    # last_name = StringField('Last Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    verify_password = PasswordField('Verify Password', validators = [DataRequired(), EqualTo('password')], description="Verify your password")
    terms = BooleanField('Terms and conditions', validators=[DataRequired()])


class ProfileUpdateForm(Form):
    full_name = StringField('Full Name', validators=[DataRequired()])
    university_id = SelectField('University', coerce=int, validators=[DataRequired()])


class PasswordResetForm(Form):
    password = PasswordField('Password', validators=[DataRequired()])
    verify_password = PasswordField('Verify Password', validators = [DataRequired(), EqualTo('password')], description="Verify your password")


class NewsletterSubscriberForm(Form):
    email = EmailField('Email Address', validators=[DataRequired(), Email()])


class CountryForm(Form):
    name = TextField('Name', validators = [DataRequired()])
    code = TextField('Code', validators = [DataRequired()])

class StateForm(Form):
    name = TextField('Name', validators = [DataRequired()])
    code = TextField('Code', validators = [DataRequired()])
    country_id = SelectField('Country', coerce=int, validators=[DataRequired()])

class CityForm(Form):
    name = StringField('Name', validators=[DataRequired()])
    url = StringField('Url', validators=[Optional()])


class PaymentOptionForm(Form):
	name = TextField('Name', validators=[DataRequired()])
	handle = TextField('Option Code', validators=[DataRequired()])
	description = TextField('Description', validators=[Optional()])
	is_enabled = BooleanField('Is Enabled', validators = [Optional()])

	def validate_name(form, field):
		if PaymentOption.query.filter(PaymentOption.name==field.data).count() != 0:
			raise ValidationError("This name is already in use")

	def validate_handle(form, field):
		if PaymentOption.query.filter(PaymentOption.handle==field.data).count() != 0:
			raise ValidationError("This code is already in use")


class UpdatePaymentOptionForm(Form):
	name = TextField('Name', validators=[DataRequired()])
	handle = TextField('Option Code', validators=[DataRequired()])
	description = TextField('Description', validators=[Optional()])
	is_enabled = BooleanField('Is Enabled', validators = [Optional()])

	def validate_name(form, field):
		if PaymentOption.query.filter(PaymentOption.name==field.data).count() != 0:
			raise ValidationError("This name is already in use")


class DeliveryOptionForm(Form):
	name = TextField('Name', validators=[DataRequired()])
	handle = TextField('Option Code', validators=[DataRequired()])
	description = TextField('Description', validators=[Optional()])

	def validate_name(form, field):
		if DeliveryOption.query.filter(DeliveryOption.name==field.data).count() != 0:
			raise ValidationError("This name is already in use")

	def validate_handle(form, field):
		if DeliveryOption.query.filter(DeliveryOption.handle==field.data).count() != 0:
			raise ValidationError("This code is already in use")



class ProductForm(Form):
	name = TextField('Name', validators = [DataRequired()], description="The name of your product")
	# handle = TextField('Url handle', validators = [DataRequired()])
	# title = TextField('Title', validators = [Optional()])
	price = FloatField('Standard Price', validators=[Optional()], default=0.0, description="Enter a numeric value. No commas allowed")
	compare_at = FloatField('Discount Price', default=0.0, validators = [Optional()], description="Enter the new discounted price. No commas allowed")
	description = TextField('Product Details', validators = [Optional()], widget=widgets.TextArea(), description="A detailed description of this product. Please ensure all Video Embeded codes are of width and height 100%.")
	caption = TextField('Short Description', validators = [Optional()], widget=widgets.TextArea(), description="A short description of your product. Please ensure all Video Embeded codes are of width and height 100%.")
	sku = TextField('SKU', validators = [Optional()], description="An internal identification number for this product")
	group_id = SelectField('Category', coerce=int, validators=[DataRequired()])
	track_stock_level = BooleanField('This product has variants (use this to specify different sizes, color etc.)', validators = [Optional()])
	quantity = FloatField('Quantity', validators = [Optional()], default=0, description="Enter a numeric value. No commas allowed")
	weight = FloatField('Weight (kg)', validators = [Optional()])
	# require_shipping = BooleanField('Require Shipping', validators = [Optional()])
	is_featured = BooleanField('Feature this product on my home page', validators = [Optional()], default=True)
	visibility = BooleanField('Display this product in my store', validators = [Optional()], default=True)
	category_id = SelectField('Directory Category', coerce=int, validators=[Optional()])
	section_id = SelectField('Directory Section', coerce=int, validators=[Optional()])
	product_custom_ids = SelectMultipleField('Add Product Custom Fields', validators=[Optional()], coerce=int, description = "Select Additional fields to best describe your product.")
	show_price = BooleanField('Display Product Price', default=True, description="Choose to display the price of the product.")
	is_private = BooleanField('Make Product Private', default=False, description="Choose to display the product to specific set of customers.")
	# is_donation = BooleanField('Flexible Pricing', default=False, description="Choose to support flexible pricing.")


	def validate_compare_at(form, field):
		if field.data > form.price.data:
			raise ValidationError("Discount cannot be more than price. Please adjust the value")

class EditProductForm(Form):
	name = TextField('Name', validators = [DataRequired()])
	# handle = TextField('Url handle', validators = [DataRequired()])
	# title = TextField('Title', validators = [Optional()])
	price = FloatField('Standard Price', validators=[Optional()], default=0.0, description="Enter a numeric value. No commas allowed")
	compare_at = FloatField('Discount Price', default=0.0, validators = [Optional()], description="Enter the new discounted price. No commas allowed")
	description = TextField('Product Details', validators = [Optional()], widget=widgets.TextArea(), description="A detailed description of this product. Please ensure all Video Embeded codes are of width and height 100%.")
	caption = TextField('Short Description', validators = [Optional()], widget=widgets.TextArea(), description="A short description of your product. Please ensure all Video Embeded codes are of width and height 100%.")
	sku = TextField('SKU', validators = [Optional()], description="An internal identification number for this product")
	group_id = SelectField('Category', coerce=int, validators=[DataRequired()])
	track_stock_level = BooleanField('This product has variants (use this to specify different sizes, color etc.', validators = [Optional()])
	quantity = FloatField('Quantity', validators = [Optional()], default=0, description="Enter a numeric value. No commas allowed")
	weight = FloatField('Weight (kg)', validators = [Optional()])
	# require_shipping = BooleanField('Require Shipping', validators = [Optional()])
	is_featured = BooleanField('Feature this product on my home page', validators = [Optional()], default=True)
	visibility = BooleanField('Display this product in my store', validators = [Optional()], default=True)
	removables = SelectMultipleField(validators=[Optional()], coerce=int)
	category_id = SelectField('Directory Category', coerce=int, validators=[Optional()])
	section_id = SelectField('Directory Section', coerce=int, validators=[Optional()])
	product_custom_ids = SelectMultipleField('Add Product Custom Fields', validators=[Optional()], coerce=int, description = "Select Additional fields to best describe your product.")
	show_price = BooleanField('Display Product Price', default=True, description="Choose to display the price of the product.")
	is_private = BooleanField('Make Product Private', default=False, description="Choose to display the product to specific set of customers.")
	# is_donation = BooleanField('Flexible Pricing', default=False, description="Choose to support flexible pricing.")


	def validate_compare_at(form, field):
		if field.data > form.price.data:
			raise ValidationError("Discount cannot be more than price. Please adjust the value")


class UpdateProductForm(EditProductForm):
	cover_image_id = IntegerField('Cover Image', widget=widgets.HiddenInput(), validators=[DataRequired()])


class VariantForm(Form):
	name = TextField('Name', validators = [DataRequired()], description="The exact description of this item (e.g. Size 44 - White)")
	sku = TextField('SKU', validators = [Optional()], description="Give an internal identification number to this item")
	price = FloatField('Price', validators =[DataRequired()], default=0, description="")
	quantity = FloatField('Quantity', validators =[Optional()], default=0)
	compare_at = FloatField('Discount', validators =[Optional()], default=0)
	# track_stock_level = BooleanField('Track stock for this entry', validators = [DataRequired()])

	def validate_compare_at(form, field):
		if field.data > form.price.data:
			raise ValidationError("Discount cannot be more than price. Please adjust the value")

class ProductVariantForm(Form):
	name = TextField('Name', validators = [DataRequired()], description="The exact description of this item (e.g. Size 44 - White)")
	sku = TextField('SKU', validators = [Optional()], description="Give an internal identification number to this item")
	price = FloatField('Price', validators =[DataRequired()], default=0, description="")
	quantity = FloatField('Quantity', validators =[Optional()], default=0)
	compare_at = FloatField('Discount', validators =[Optional()], default=0)
	product_id = SelectField('Product Id', coerce=int, validators=[DataRequired()])

	# track_stock_level = BooleanField('Track stock for this entry', validators = [DataRequired()])

	def validate_compare_at(form, field):
		if field.data > form.price.data:
			raise ValidationError("Discount cannot be more than price. Please adjust the value")


class PageFilterForm(Form):
	q = TextField("Search Query", validators=[Optional()])
	search_in = TextField("Search Query", validators=[Optional()])
	page = IntegerField("Page", default=1, validators=[validators.NumberRange(min=1)])
	order_by = TextField("Order By", default="last_updated", validators=[validators.AnyOf(['cart_price', 'date_created', 'last_updated', 'name', 'price-high-to-low', 'price-low-to-high'])])
	size = IntegerField("Limit", default=60, validators=[validators.NumberRange(min=1, max=120)])
	# min_price = FloatField("Min Price", default=1, validators=[validators.NumberRange(min=0, max=150000)])
	# max_price = FloatField("Max Price", default=150000, validators=[validators.NumberRange(min=0, max=150000)])
	available_only = BooleanField("Available Only", default=False)
	section_id = IntegerField("Section", default=0)
	tag_id = IntegerField("Tag", default=0)
	# sizes = StringListField('Sizes', default=[])
	category_id = StringListField('Categories', default=[])
	location=TextField("Location", validators=[Optional()])
	# categories = IntegerListField('Sizes', default=[])
	# groups = IntegerListField('Sizes', default=[])


class OrderStatusForm(Form):
	order_status_id = SelectField('Status', coerce=int, validators=[DataRequired()])
	all_entries = BooleanField('Set status for all entries', validators=[Optional()])

class TransactionStatusForm(Form):
	transaction_status_id = SelectField('Status', coerce=int, validators=[DataRequired()])

class DeliveryStatusForm(Form):
	delivery_status_id = SelectField('Status', coerce=int, validators=[DataRequired()])



class DirSectionForm(Form):
	name = TextField("Name", validators=[DataRequired()])
	position = IntegerField("Position", default=0, validators=[Optional()])
	slug = TextField("Slug", validators = [Optional()], description = "text by which the system identifies this section; text should be in lower case without spaces")
	description = TextField("Description", validators=[Optional()], description = "A short description of this section")
	sla_type = SelectField("SLA Refund Type", validators=[Optional()], coerce=str, description = "Please Select Type of SLA")
	sla_refund_period = IntegerField("SLA Refund Time Period", validators=[Optional()])

class DirCategoryForm(Form):
	name = TextField("Name", validators=[DataRequired()])
	position = IntegerField("Position", default=0, validators=[Optional()])
	slug = TextField("Value", validators = [DataRequired()], description = "text by which the system identifies this category; text should be in lower case without spacesces")
	section_id = SelectField("Section", coerce=int, validators=[DataRequired()])
	description = TextField("Description", validators=[Optional()], description = "A short description of this category")
	show_on_grocery = BooleanField("Display On Grocery", description="Choose to display this Product Category on the Groceries Directory", validators=[Optional()])

class DirCategoryTagForm(Form):
	"""docstring for DirCategoryTagForm"""
	name = TextField("Name", validators=[DataRequired()])
	url = TextField("URL", validators=[Optional()])
	description = TextField("Description", validators=[Optional()], description = "A short description of this Tag")
	category_id = SelectField("Product Category", coerce=int, validators=[DataRequired()])
	search_category_id = SelectField("Optional Target Category", coerce=int, validators=[Optional()])
	section_id = SelectField("Optional Target Section", coerce=int, validators=[Optional()])
	tag_key = TextField("Tag Key", validators=[Optional()])
	is_redirect = BooleanField('Choose to Redirect Tag to different Location', validators = [Optional()], default=False)
	search_query = TextField("Search Query", validators=[Optional()])
	app_exclusion_lists_ids = SelectMultipleField('Exclusion List', validators=[Optional()], coerce=int)

	def validate_is_redirect(form, field):
		if field.data==True and form.url.data=="":
			raise ValidationError("Please specify URL to redirect to")

		if field.data==False and form.search_query.data=="":
			raise ValidationError("Please specify Search query for the Tag")


class UploadForm(Form):
	name = TextField("Name", validators=[Optional()])
	alt_text = TextField("Alt Text", validators=[Optional()])
	url = TextField("URL", validators=[Optional()])
	product_id = IntegerField("Product", validators=[Optional()])
	service_id = IntegerField("Service", validators=[Optional()])
	banner_id = IntegerField("Banner", validators=[Optional()])


class FilterForm(Form):
	name = TextField("Name", validators=[DataRequired()])
	category_id = SelectField('Category Id', coerce=int,validators=[DataRequired()])

class FilterOptionForm(Form):
	name = TextField("Name", validators=[DataRequired()])
	filter_id = SelectField('Filter Id', coerce=int,validators=[DataRequired()])
	values = TextField("Values", validators=[Optional()])


class ContactForm(Form):
	name = TextField('Full Name', validators = [DataRequired()])
	subject = TextField('Subject', validators = [DataRequired()])
	email = EmailField('Email Address', validators = [DataRequired(),Email()])
	phone = TextField('Phone Number', validators = [DataRequired()])
	body = TextField('Message', validators = [DataRequired()], widget=widgets.TextArea())
	captcha = RecaptchaField(public_key=app.config.get("RECAPTCHA_PUB_KEY"), private_key=app.config.get("RECAPTCHA_PRIV_KEY"), secure=True)


class ComplaintForm(Form):
	name = TextField('Full Name', validators = [DataRequired()])
	email = EmailField('Email Address', validators = [DataRequired(),Email()])
	phone = TextField('Phone Number', validators = [Optional()])
	reason = TextField('Reason', validators = [DataRequired()], widget=widgets.TextArea())
	captcha = RecaptchaField(public_key=app.config.get("RECAPTCHA_PUB_KEY"), private_key=app.config.get("RECAPTCHA_PRIV_KEY"), secure=True)

class ReplyForm(Form):
	message = TextField('Reply Message', validators = [DataRequired()], widget=widgets.TextArea())


class MessageForm(Form):
	name = TextField("Name", validators=[DataRequired()])
	email = TextField("Email", validators=[DataRequired()])
	phone = TextField("Phone", validators=[DataRequired()])
	subject = TextField("Subject", validators=[Optional()])
	is_read = BooleanField("is read", validators=[Optional()])
	is_replied = BooleanField("is replied", validators=[Optional()])
	date_replied = DateTimeField("Date Replied", validators=[Optional()])
	body = TextField("Body", validators=[Optional()]) # for plain text messages

class AdminMessageForm(MessageForm): pass


class SearchForm(Form):
    state_id = SelectField('State', coerce=int,validators=[Optional()])
    university_id = SelectField('University', coerce=int,validators=[Optional()])
    section_id = SelectField('Section', coerce=int,validators=[Optional()])
    category_id = SelectField('Category', coerce=int,validators=[Optional()])
    search_q = TextField("Term", validators=[Optional()])


class BlankForm(Form): pass
