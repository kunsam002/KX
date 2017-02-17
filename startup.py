
import os, pytz, json
from datetime import datetime, timedelta
from kx.models import *
from kx.services import *
from kx import app, db, logger
from sqlalchemy import or_, and_

SETUP_DIR = app.config.get("SETUP_DIR") # Should be present in config



def update_access_group_roles(group_id, *role_ids):
	"""
	Adds the selected roles to the an access group

	:param group_id: AccessGroup ID
	:param role_ids: One or more role ids
	"""

	access_group = AccessGroup.query.get(group_id)

	if not access_group:
		raise Exception("AccessGroup not found")

	role_names = []
	role_ids = list(role_ids)
	_role_ids = role_ids
	for x in _role_ids:
		if not isinstance(x, (int, float, long)):
			role_names.append(x)
			role_ids = [r for r in role_ids if r is not x]

	queries = []
	if role_ids:
		queries.append(Role.id.in_(role_ids))

	if role_names:
		queries.append(Role.name.in_(role_names))

	roles = Role.query.filter(or_(*queries)).all()
	access_group.roles = roles
	db.session.add(access_group)
	try:
		db.session.commit()
		return access_group
	except:
		db.session.rollback()
		raise


def add_user_to_access_group(user_id, group):
	"""
	Adds a user to an access group

	:param user_id: The User ID
	:param group: AccessGroup ID or Name

	returns: kx.models.User
	"""

	user = User.query.get(user_id)

	if not user:
		raise Exception("User not found")

	return user.add_access_group(group)


def add_user_to_role(user_id, role):
	"""
	Adds a user to a role

	:param user_id: The User ID
	:param role: Role ID or Name

	returns: kx.models.User
	"""

	user = User.query.get(user_id)

	if not user:
		raise Exception("User not found")

	return user.add_role(role)


def build_restricted_domains():
	""" Creates a list of restricted domains that merchants can't use """

	restricted_domains = app.config.get("RESTRICTED_DOMAINS") # mandatory

	for d in restricted_domains:
		r = RestrictedDomain(domain=d.strip().lower())
		db.session.add(r)
		try:
			db.session.commit()
		except:
			db.session.rollback()
			raise

	logger.info("Created Restricted Domains")



def generate_super_admin():
	""" Creates the super admin user account """

	username = app.config.get("ADMIN_USERNAME") # mandatory
	password = app.config.get("ADMIN_PASSWORD") # mandatory
	email = app.config.get("ADMIN_EMAIL") # mandatory
	full_name = app.config.get("ADMIN_FULL_NAME") # mandatory

	user = User(username=username, password=password, email=email, full_name=full_name, is_active=True, is_super_admin=True, is_verified=True, is_staff=True, is_admin=True)
	db.session.add(user)
	db.session.commit()

	add_user_to_access_group(user.id, "super_admin")

	logger.info("Created Super Admin User")



def load_access_groups():
	""" Loads all access groups into the database """
	src = os.path.join(SETUP_DIR, "access_groups.json")
	f = open(src)
	data = json.loads(f.read().encode("UTF-8"))
	try:
		for d in data:
			obj = AccessGroup(**d)
			db.session.add(obj)
		db.session.commit()
		logger.info("Loaded All Access Groups.")
	except:
		db.session.rollback()
		raise


def build_default_access_groups():
	""" Creates the default level access groups """

	logger.info("Building default access groups" )
	access_group = AccessGroup.query.filter(AccessGroup.name=="super_admin").one()

	update_access_group_roles(access_group.id, "super_admin")



def load_countries():
	""" Loads all countries into the database """
	src = os.path.join(SETUP_DIR, "countries.json")
	f = open(src)
	data = json.loads(f.read().encode("UTF-8"))
	try:
		for d in data:
			obj = Country(**d)
			db.session.add(obj)
		db.session.commit()
		logger.info("Loaded All Countries.")
	except:
		db.session.rollback()
		raise


def load_currencies():
	""" loads all currencies into the database """
	src = os.path.join(SETUP_DIR, "currencies.json")
	f = open(src)
	data = json.loads(f.read().encode("UTF-8"))
	try:
		for d in data:
			obj = Currency(**d)
			db.session.add(obj)
		db.session.commit()
		logger.info("Loaded All Currencies.")
	except:
		db.session.rollback()
		raise


def load_roles():
	""" Loads all roles into the database """
	src = os.path.join(SETUP_DIR, "roles.json")
	logger.info(src)
	f = open(src)
	data = json.loads(f.read().encode("UTF-8"))
	try:
		for d in data:
			obj = Role(**d)
			db.session.add(obj)
		db.session.commit()
		logger.info("Loaded All Roles.")
	except:
		db.session.rollback()
		raise


def load_timezones():
	""" loads all timezones into the database """
	src = os.path.join(SETUP_DIR, "timezones.json")
	f = open(src)
	data = json.loads(f.read().encode("UTF-8"))
	try:
		for d in data:
			obj = Timezone(**d)
			db.session.add(obj)
		db.session.commit()
		logger.info("Loaded All Timezones.")
	except:
		db.session.rollback()
		raise


def load_universities():
	""" loads all universities into the database """
	src = os.path.join(SETUP_DIR, "universities.json")
	f = open(src)
	data = json.loads(f.read().encode("UTF-8"))
	try:
		for d in data:
			s = State.query.filter(State.code==d.pop("state_code")).first()
			if not s:
				logger.info(d)
			else:
				d["state_id"] = s.id
				obj = University(**d)
				db.session.add(obj)
		db.session.commit()
		logger.info("Loaded All Universities.")
	except:
		db.session.rollback()
		raise


def load_state(c_name, s_file):
	""" Loads a state file into the specified country """

	country = Country.query.filter(Country.slug==c_name.lower()).first()

	if not country:
		return

	data = json.loads(open(s_file).read().encode("UTF-8"))

	try:
		for code, name in data.items():
			state = State(name=name, code=code, country=country)
			db.session.add(state)
		db.session.commit()

		logger.info("Loaded states for %s" % country.name)
		return country
	except:
		db.session.rollback()
		raise


def load_states():
	""" Loads all states into the database by matching it with their corresponding countries """
	states_dir = os.path.join(SETUP_DIR, "states")
	for root, dirs, files in os.walk(states_dir):
		try:
			_files = [_f for _f in files if ".json" in _f]
			for f in _files:
				c_name = f.replace(".json", "")
				s_file = os.path.join(states_dir, f)
				country = load_state(c_name, s_file)

		except:
			db.session.rollback()
			raise


def create_cities():
	from kx import db, models, logger
	from kx.models import State, City

	lga = {1: ['Aba North','Aba South','Arochukwu','Bende','Ikwuano','Isiala Ngwa North','Isiala Ngwa South','Isuikwuato','Obi Ngwa','Ohafia','Osisioma','Ugwunagbo','Ukwa East','Ukwa West','Umuahia North','Umuahia South','Umu Nneochi'],
		2: ['Demsa','Fufure','Ganye','Gayuk','Gombi','Grie','Hong','Jada','Larmurde','Madagali','Maiha','Mayo Belwa','Michika','Mubi North','Mubi South','Numan','Shelleng','Song','Toungo','Yola North','Yola South'],
		3: ['Abak','Eastern Obolo','Eket','Esit Eket','Essien Udim','Etim Ekpo','Etinan','Ibeno','Ibesikpo Asutan','Ibiono-Ibom','Ika','Ikono','Ikot Abasi','Ikot Ekpene','Ini','Itu','Mbo','Mkpat-Enin','Nsit-Atai','Nsit-Ibom','Nsit-Ubium','Obot Akara','Okobo','Onna','Oron','Oruk Anam','Udung-Uko','Ukanafun','Uruan','Urue-Offong/Oruko','Uyo'],
		4: ['Aguata','Anambra East','Anambra West','Anaocha','Awka North','Awka South','Ayamelum','Dunukofia','Ekwusigo','Idemili North','Idemili South','Ihiala','Njikoka','Nnewi North','Nnewi South','Ogbaru','Onitsha North','Onitsha South','Orumba North','Orumba South','Oyi'],
		5: ['Alkaleri','Bauchi','Bogoro','Damban','Darazo','Dass','Gamawa','Ganjuwa','Giade','Itas/Gadau',"Jama''are",'Katagum','Kirfi','Misau','Ningi','Shira','Tafawa Balewa','Toro','Warji','Zaki'],
		6: ['Brass','Ekeremor','Kolokuma/Opokuma','Nembe','Ogbia','Sagbama','Southern Ijaw','Yenagoa'],
		7: ['Agatu','Apa','Ado','Buruku','Gboko','Guma','Gwer East','Gwer West','Katsina-Ala','Konshisha','Kwande','Logo','Makurdi','Obi, Benue State','Ogbadibo','Ohimini','Oju','Okpokwu','Oturkpo','Tarka','Ukum','Ushongo','Vandeikya'],
		8: ['Abadam','Askira/Uba','Bama','Bayo','Biu','Chibok','Damboa','Dikwa','Gubio','Guzamala','Gwoza','Hawul','Jere','Kaga','Kala/Balge','Konduga','Kukawa','Kwaya Kusar','Mafa','Magumeri','Maiduguri','Marte','Mobbar','Monguno','Ngala','Nganzai','Shani'],
		9: ['Abi','Akamkpa','Akpabuyo','Bakassi','Bekwarra','Biase','Boki','Calabar Municipal','Calabar South','Etung','Ikom','Obanliku','Obubra','Obudu','Odukpani','Ogoja','Yakuur','Yala'],
		10: ['Aniocha North','Aniocha South','Bomadi','Burutu','Ethiope East','Ethiope West','Ika North East','Ika South','Isoko North','Isoko South','Ndokwa East','Ndokwa West','Okpe','Oshimili North','Oshimili South','Patani','Sapele, Delta','Udu','Ughelli North','Ughelli South','Ukwuani','Uvwie','Warri North','Warri South','Warri South West'],
		11: ['Abakaliki','Afikpo North','Afikpo South','Ebonyi','Ezza North','Ezza South','Ikwo','Ishielu','Ivo','Izzi','Ohaozara','Ohaukwu','Onicha'],
		12: ['Akoko-Edo','Egor','Esan Central','Esan North-East','Esan South-East','Esan West','Etsako Central','Etsako East','Etsako West','Igueben','Ikpoba Okha','Orhionmwon','Oredo','Ovia North-East','Ovia South-West','Owan East','Owan West','Uhunmwonde'],
		13: ['Ado Ekiti','Efon','Ekiti East','Ekiti South-West','Ekiti West','Emure','Gbonyin','Ido Osi','Ijero','Ikere','Ikole','Ilejemeje','Irepodun/Ifelodun','Ise/Orun','Moba','Oye'],
		14: ['Aninri','Awgu','Enugu East','Enugu North','Enugu South','Ezeagu','Igbo Etiti','Igbo Eze North','Igbo Eze South','Isi Uzo','Nkanu East','Nkanu West','Nsukka','Oji River','Udenu','Udi','Uzo Uwani'],
		15: ['Abaji','Bwari','Gwagwalada','Kuje','Kwali','Municipal Area Council'],
		16: ['Akko','Balanga','Billiri','Dukku','Funakaye','Gombe','Kaltungo','Kwami','Nafada','Shongom','Yamaltu/Deba'],
		17: ['Aboh Mbaise','Ahiazu Mbaise','Ehime Mbano','Ezinihitte','Ideato North','Ideato South','Ihitte/Uboma','Ikeduru','Isiala Mbano','Isu','Mbaitoli','Ngor Okpala','Njaba','Nkwerre','Nwangele','Obowo','Oguta','Ohaji/Egbema','Okigwe','Orlu','Orsu','Oru East','Oru West','Owerri Municipal','Owerri North','Owerri West','Unuimo'],
		18: ['Auyo','Babura','Biriniwa','Birnin Kudu','Buji','Dutse','Gagarawa','Garki','Gumel','Guri','Gwaram','Gwiwa','Hadejia','Jahun','Kafin Hausa','Kazaure','Kiri Kasama','Kiyawa','Kaugama','Maigatari','Malam Madori','Miga','Ringim','Roni','Sule Tankarkar','Taura','Yankwashi'],
		19: ['Birnin Gwari','Chikun','Giwa','Igabi','Ikara','Jaba',"Jema''a",'Kachia','Kaduna North','Kaduna South','Kagarko','Kajuru','Kaura','Kauru','Kubau','Kudan','Lere','Makarfi','Sabon Gari','Sanga','Soba','Zangon Kataf','Zaria'],
		20: ['Ajingi','Albasu','Bagwai','Bebeji','Bichi','Bunkure','Dala','Dambatta','Dawakin Kudu','Dawakin Tofa','Doguwa','Fagge','Gabasawa','Garko','Garun Mallam','Gaya','Gezawa','Gwale','Gwarzo','Kabo','Kano Municipal','Karaye','Kibiya','Kiru','Kumbotso','Kunchi','Kura','Madobi','Makoda','Minjibir','Nassarawa, Kano State','Rano','Rimin Gado','Rogo','Shanono','Sumaila','Takai','Tarauni','Tofa','Tsanyawa','Tudun Wada','Ungogo','Warawa','Wudil'],
		21: ['Bakori','Batagarawa','Batsari','Baure','Bindawa','Charanchi','Dandume','Danja','Dan Musa','Daura','Dutsi','Dutsin Ma','Faskari','Funtua','Ingawa','Jibia','Kafur','Kaita','Kankara','Kankia','Katsina','Kurfi','Kusada',"Mai''Adua",'Malumfashi','Mani','Mashi','Matazu','Musawa','Rimi','Sabuwa','Safana','Sandamu','Zango'],
		22: ['Aleiro','Arewa Dandi','Argungu','Augie','Bagudo','Birnin Kebbi','Bunza','Dandi','Fakai','Gwandu','Jega','Kalgo','Koko/Besse','Maiyama','Ngaski','Sakaba','Shanga','Suru','Wasagu/Danko','Yauri','Zuru'],
		23: ['Adavi','Ajaokuta','Ankpa','Bassa, Kogi State','Dekina','Ibaji','Idah','Igalamela Odolu','Ijumu','Kabba/Bunu','Kogi','Lokoja','Mopa Muro','Ofu','Ogori/Magongo','Okehi','Okene','Olamaboro','Omala','Yagba East','Yagba West'],
		24: ['Asa','Baruten','Edu','Ekiti, Kwara State','Ifelodun, Kwara State','Ilorin East','Ilorin South','Ilorin West','Irepodun, Kwara State','Isin','Kaiama','Moro','Offa','Oke Ero','Oyun','Pategi'],
		25: ['Alimosho Akowonjo','Agege Sango','Ajeromi Ifelodun Ajegunle','Apapa','Amuwo Odofin','Badagry','Ita-Maru Epe','Igbo-Ifon, Eti Osa West','Ibeju-Lekki','Ifako Ijaiye','Ikeja','Ikorodu','Kosofe Ojota','Lagos Mainland, Ebute-Metta','Lagos Island, Isale-Eko','Mushin','Ojo','Oshodi Isolo','Shomolu','Surulere','Abule Egba, Agbado Okeodo','Alapere, Ketu','Badiya, Apapa Iganmu','Ayobo, Ipaja','Badagry West Kankon','Pedro Bariga','Coker Aguda','Isheri-Olofin, Egbe Idimu','Eredo, Epe/Ijebu','Oyonka, Iba','Eti-Osa East, Ajah','Ifelodun, Amukoko','Igbogbo Baiyeku','Ijede, Maidan','Odogunyan, Ikorodu North','Owutu, Ikorodu West','Ikosi Ejinrin, Agbowa','Ikosi Isheri','Igando, Ikotun','Ikoyi Obalende','Imota Ebute-Ajebo','Iru-Victoria Island','Isolo','Ikate Itire','Kakawa, Lagos Island East','Mosan Okunola','Odi-Olowo, Ilupeju','Oke-Ira, Ojodu','Ojokoro, Ijaye','Olorunda, Iworo','Onigbongbo, Opebi','Oriade Ijegun-Ibasa','Abekoko, Orile Agege','Oto Awori, Ijaniki','Adekunle, Yaba'],
		26: ['Akwanga','Awe','Doma','Karu','Keana','Keffi','Kokona','Lafia','Nasarawa','Nasarawa Egon','Obi, Nasarawa State','Toto','Wamba'],
		27: ['Agaie','Agwara','Bida','Borgu','Bosso','Chanchaga','Edati','Gbako','Gurara','Katcha','Kontagora','Lapai','Lavun','Magama','Mariga','Mashegu','Mokwa','Moya','Paikoro','Rafi','Rijau','Shiroro','Suleja','Tafa','Wushishi'],
		28: ['Abeokuta North','Abeokuta South','Ado-Odo/Ota','Egbado North','Egbado South','Ewekoro','Ifo','Ijebu East','Ijebu North','Ijebu North East','Ijebu Ode','Ikenne','Imeko Afon','Ipokia','Obafemi Owode','Odeda','Odogbolu','Ogun Waterside','Remo North','Shagamu'],
		29: ['Akoko North-East','Akoko North-West','Akoko South-West','Akoko South-East','Akure North','Akure South','Ese Odo','Idanre','Ifedore','Ilaje','Ile Oluji/Okeigbo','Irele','Odigbo','Okitipupa','Ondo East','Ondo West','Ose','Owo'],
		30: ['Atakunmosa East','Atakunmosa West','Aiyedaade','Aiyedire','Boluwaduro','Boripe','Ede North','Ede South','Ife Central','Ife East','Ife North','Ife South','Egbedore','Ejigbo','Ifedayo','Ifelodun','Ila','Ilesa East','Ilesa West','Irepodun','Irewole','Isokan','Iwo','Obokun','Odo Otin','Ola Oluwa','Olorunda','Oriade','Orolu','Osogbo'],
		31: ['Afijio','Akinyele','Atiba','Atisbo','Egbeda','Ibadan North','Ibadan North-East','Ibadan North-West','Ibadan South-East','Ibadan South-West','Ibarapa Central','Ibarapa East','Ibarapa North','Ido','Irepo','Iseyin','Itesiwaju','Iwajowa','Kajola','Lagelu','Ogbomosho North','Ogbomosho South','Ogo Oluwa','Olorunsogo','Oluyole','Ona Ara','Orelope','Ori Ire','Oyo','Oyo East','Saki East','Saki West','Surulere, Oyo State'],
		32: ['Bokkos','Barkin Ladi','Bassa','Jos East','Jos North','Jos South','Kanam','Kanke','Langtang South','Langtang North','Mangu','Mikang','Pankshin',"Qua''an Pan",'Riyom','Shendam','Wase'],
		33: ['Abua/Odual','Ahoada East','Ahoada West','Akuku-Toru','Andoni','Asari-Toru','Bonny','Degema','Eleme','Emuoha','Etche','Gokana','Ikwerre','Khana','Obio/Akpor','Ogba/Egbema/Ndoni','Ogu/Bolo','Okrika','Omuma','Opobo/Nkoro','Oyigbo','Port Harcourt','Tai'],
		34: ['Binji','Bodinga','Dange Shuni','Gada','Goronyo','Gudu','Gwadabawa','Illela','Isa','Kebbe','Kware','Rabah','Sabon Birni','Shagari','Silame','Sokoto North','Sokoto South','Tambuwal','Tangaza','Tureta','Wamako','Wurno','Yabo'],
		35: ['Ardo Kola','Bali','Donga','Gashaka','Gassol','Ibi','Jalingo','Karim Lamido','Kumi','Lau','Sardauna','Takum','Ussa','Wukari','Yorro','Zing'],
		36: ['Bade','Bursari','Damaturu','Fika','Fune','Geidam','Gujba','Gulani','Jakusko','Karasuwa','Machina','Nangere','Nguru','Potiskum','Tarmuwa','Yunusari','Yusufari'],
		37: ['Anka','Bakura','Birnin Magaji/Kiyaw','Bukkuyum','Bungudu','Gummi','Gusau','Kaura Namoda','Maradun','Maru','Shinkafi','Talata Mafara','Chafe','Zurmi']}

	state_code={'Abia':1,'Adamawa':2,'Akwa Ibom':3,'Anambra':4,'Bauchi':5,'Bayelsa':6,'Benue':7,'Borno':8,'Cross River':9,'Delta':10,'Ebonyi':11,'Edo':12,'Ekiti':13,'Enugu':14,'Abuja':15,'Gombe':16,'Imo':17,'Jigawa':18,'Kaduna':19,'Kano':20,'Katsina':21,'Kebbi':22,'Kogi':23,'Kwara':24,'Lagos':25,'Nassarawa':26,'Niger':27,'Ogun':28,'Ondo':29,'Osun':30,'Oyo':31,'Plateau':32,'Rivers':33,'Sokoto':34,'Taraba':35,'Yobe':36,'Zamfara':37}

	for s in State.query.all():
		for i in lga[state_code[s.name]]:
			obj = City(name= i,state_id= s.id, country_id=s.country_id)
			db.session.add(obj)
			db.session.commit()


def start():
	""" Start the setup process """
	# load_roles()
	# load_access_groups()
	# build_default_access_groups()
	# build_restricted_domains()
	# generate_super_admin()
	load_timezones()
	# load_currencies()
	load_countries()
	load_states()
	create_cities()
	load_universities()
