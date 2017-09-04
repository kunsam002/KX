# from factories import create_app
# import socket
import time
import logging
# import time
# from daemon import runner
import os
from datetime import datetime
import time

os.chdir('/opt/kx')

from factories import create_app

app_ = create_app('monitor', 'config.MicroTestConfig')

with app_.app_context():
    from kx import celery
    from kx import logger
    import time

    interval = app_.config.get("CELERY_MONITOR_INTERVAL", 120)
    delay = app_.config.get("CELERY_MONITOR_DELAY", 60)

    logger.info("Celery Monitoring starting")
    retries = 0

    while retries < 10:

        result = ping.delay()
        time.sleep(delay)

        if result.ready():
            retries = 0
            print("Celery is alive %s " % datetime.now())
        else:
            retries += 1
            print "celery did not respond in %s seconds %s retries: %s" % (interval + delay, datetime.now(), retries)
            os.system("service celery restart")
        print globals()['time']
        globals()['time'].sleep(interval)

    notify_celery_failure()
