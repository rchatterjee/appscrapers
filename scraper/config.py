"""Keep all the variables here that one plans to tweak or can tweak.
The db is always augmented based on appid and term. So don't worry to
double run the same script. Modification to this file will only update
the db, and it will not start from scratch or delete anything.
"""


import time
from pathlib import Path
import os

THIS_DIR = Path(__file__).absolute().parent
BASE_DIR = THIS_DIR.parent
DATA_DIR = BASE_DIR / 'data'

# Where does the js server logs its output
JS_SERVER_LOG_FILE = "/tmp/jsserver.log"
SOCK_PATH = "/tmp/ipv-spyware"
SITE_SPECIFIC = ['site:play.google.com', 'site:itunes.apple.com']

LANG =  os.environ.get('APP_LANG', 'en')
COUNTRY = os.environ.get('APP_COUNTRY', 'us')

def now():
    return time.strftime("%Y%m%d:%H%M")


def timestamp():
    return int(time.time())


# DB
# DB_FILE = DATA_DIR / "apps.db"
DB_FILE = str(DATA_DIR / "crawled_apps.db")
TEST_DB_FILE = str(DATA_DIR / "apps_test.db")
BACKUP_DB = str(DATA_DIR / "apps.db.bak")

# Download settings
THROTTLE_DEFAULT = 5   # xx requests per second
APPS_PER_QUERY = 50    # Download 50 apps per search term
NUM_COMMENTS_TO_DOWNLOAD = 200  # Max 200 comments to download
# COMMENT_SORT_CRITERIA : NEWEST (defailt) If you need to change that change in server.js

CLOSURE_SIZE_LIMIT = 1000  # The closure function should giveup after these many points in the set

# Logging
import logging
import logging.handlers
_log = None
LOG_FILENAME = 'appscraper.log'
LOGGER = 'appscraper'

import numpy as np
def sleep_time(lam=1.0):
    """Sample sleeping time from a poisson distribution"""
    time.sleep(np.random.poisson(lam))

def setup_logger():
    global _log
    if _log is None:
        logging.getLogger('zerorpc').setLevel(logging.WARNING)
        logging.basicConfig(
            format="[%(filename)s:%(lineno)s] - %(name)s - %(levelname)s - %(message)s",
            level=logging.DEBUG,
            filename=LOG_FILENAME
        )
        # _log = logging.getLogger(LOGGER)
        # _log.setLevel(logging.DEBUG)
        # ha
        # ndler = logging.handlers.RotatingFileHandler(
        #     LOG_FILENAME, maxBytes=1024*1024*2, backupCount=1)
        # _log.addHandler(handler)
        logging.info("---------------------Starting Logger--------------------")
        _log = True
    return logging
