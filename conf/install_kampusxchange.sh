#!/bin/sh
# @Author: kunsam002
# @Date:   2017-09-01
# @Last Modified by:   Olukunle Ogunmokun
# @Last Modified time: 2017-09-01

# copy uwsgi.conf to upstart
sudo cp uwsgi.conf /etc/init/
sudo ln -s /lib/init/upstart-job /etc/init.d/uwsgi

# copy celery.conf to upstart
sudo cp celery.conf /etc/init/
sudo ln -s /lib/init/upstart-job /etc/init.d/celery

# create necessary uwsgi folders
sudo mkdir -p /var/log/uwsgi
sudo mkdir -p /etc/uwsgi/apps-enabled
sudo mkdir -p /etc/uwsgi/apps-available

# necessary log folder for logging
sudo mkdir -p /var/log/smemarkethub
sudo mkdir -p /var/log/nginx/smemarkethub
sudo chown -R g2trust.g2trust /var/log/smemarkethub
sudo chown -R g2trust.g2trust /var/log/nginx

# create necessary symbolic links for uwsgi
sudo ln -s /opt/SME/conf/uwsgi/main.ini /etc/uwsgi/apps-enabled
sudo ln -s /opt/SME/conf/uwsgi/admin.ini /etc/uwsgi/apps-enabled
sudo ln -s /opt/SME/conf/uwsgi/backend.ini /etc/uwsgi/apps-enabled

# create necessary symbolic links for nginx
sudo ln -s /opt/SME/conf/nginx/smemarkethub.com /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default


# Restart nginx server
sudo service nginx restart