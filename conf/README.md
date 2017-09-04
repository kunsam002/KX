How to configure the flask production app using nginx and uwsgi
===============================================================

1. Download uwsgi using pip. If the python-dev and other utils aren't setup (use apt-get in ubuntu)
2. Configure the uwsgi/emperor setup using the uwsgi.conf file. The contents are as follows

This file should be located in /etc/init/uwsgi.conf

####################
UWSGI upstart config
####################

description "Traclist Main"
start on runlevel [2345]
stop on runlevel [06]
respawn

env UWSGI=/usr/local/bin/uwsgi
env LOGTO=/var/log/uwsgi/emperor.log


exec $UWSGI --master --emperor /etc/uwsgi/apps-enabled --die-on-term --uid traclist --gid traclist --logto $LOGTO

############
create an upstart job for uwsgi

using:

sudo ln -s /lib/init/upstart-job /etc/init.d/uwsgi
############

3. create the following folders
 sudo mkdir -p /var/log/uwsgi
 sudo mkdir -p /etc/uwsgi/apps-enabled
 sudo mkdir -p /etc/uwsgi/apps-available

4. Copy (or symlink) your uwsgi config file into /var/uwsgi/apps-enabled
	(symlink version)
	sudo ln -s conf/admin.ini /etc/uwsgi/apps-enabled
	sudo ln -s conf/main.ini /etc/uwsgi/apps-enabled
	sudo ln -s conf/backend.ini /etc/uwsgi/apps-enabled

5.  Change the default user for nginx workers to match the same user as specified in your app.
	This is setup in the /etc/nginx/nginx.conf file. Change the "user www-data" to "user traclist" (an example)

	

########################
myapp.ini should contain
########################

[uwsgi]
base = /path/to/your/python/app/
app = app
pythonpath = %(base)
socket = /tmp/app/%n.sock
module = main
workers = 4
chdir = %(base)



5. install nginx using apt-get or by downloading the latest source and building it
6. setup your nginx site config file and copy (or symlink) the file to:
	/etc/nginx/sites-enabled/

	symlink ex.
	ln -s /path/to/your/nginx/site/config /etc/nginx/sites-available/config





