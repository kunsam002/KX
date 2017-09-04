#! /usr/bin/env python
"""
tasks_run.py

New celery tasks app to execute via python. Hopefully this will fix the long standing celery that has driven me crazy!
"""

from __future__ import absolute_import, unicode_literals

import eventlet

eventlet.monkey_patch()

import os
from factories import create_app, initialize_api, initialize_blueprints
from celery.bin import worker
import getopt
import sys


# worker1_options = {
# 	"loglevel": "INFO",
# 	"trackback": True,
# 	"events": True,
# 	"autoscale": "100,20",
# 	"beat": True,
# 	"autoreload": True,
# 	'pool': 'eventlet',
# }



def main(config_file='config.TestSiteProdConfig', argv=None):
    app = create_app('sme', config_file)

    with app.app_context():
        from kx import celery
        from kx.models import *
        from kx.services import *

        celery_app = app.celery

        worker1 = worker.worker(app=celery_app)
        # worker2 = worker.worker(app=celery_app)

        worker1.run_from_argv('worker', argv=argv)
    # worker2.run(**worker2_options)


if __name__ == "__main__":
    config_file = sys.argv[1]

    args = sys.argv[2:]

    # config_file = 'config.TestSiteProdConfig'

    # if len(args) > 0:
    # 	config_file = str(args[0])

    main(config_file, args)
