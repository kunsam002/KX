import os
import uwsgi
import gevent.monkey
import socket

#gevent.monkey.patch_all()

from factories import create_app, initialize_api, initialize_blueprints

app = create_app('sme', 'config.SiteProdConfig')

with app.app_context():
	from kx.views.public import www
	from kx import api, principal
	from kx.resources import resource

	# Initialize the app blueprints
	initialize_blueprints(app, www)
	initialize_api(app, api)


if __name__ == "__main__":

	port = int(os.environ.get('PORT', 5000))
	app.run(host='0.0.0.0', port=port)
