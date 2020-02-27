"""
File to connect to the js server server.js that scrapes both Play Store and iTune App Store.
"""
import subprocess
import zerorpc
from . import config
import time
import os

sock_path_prefix = config.SOCK_PATH
pythonc = None
__package__ = ['scraper.appstore_api']

def connect(store, fresh=False):
    global pythonc
    sock_path = '{}_{}.sock'.format(sock_path_prefix, store)
    assert store in ('android', 'ios'), "Store={!r} not supported".format(store)
    server_js_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'server.js'
    )
    if fresh:  # Kill the process
        subprocess.run('kill -9 `lsof -t {}`'.format(sock_path),
                       shell=True)
        time.sleep(1)
        os.remove(sock_path)

    if not os.path.exists(sock_path):
        print("Starting js server: {}".format(server_js_path))
        # --max-old-space-size=8192 means, Node can use upto 8192mb space.  
        jsprog = subprocess.Popen(
            'node --max-old-space-size=8192 {0} {1} 1>>{2} 2>&1 &'
            .format(server_js_path, store, config.JS_SERVER_LOG_FILE),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )  # start if not already running, use memoization benefits
        time.sleep(0.01)

    # python client
    pythonc = zerorpc.Client()
    # pythonc.connect('tcp://0.0.0.0:4242')
    pythonc.connect('ipc://{}'.format(sock_path))


def get_store_func(func_name, store):
    # It is dangerous to use eval, but this is a cute little script,
    # so I am doing it.
    if pythonc is None:
        connect(store)
    return eval('pythonc.{}_{}'.format(store,func_name))


def app_page(appid, store='android'):
    assert store == 'android', "Not supported for other store={}".format(store)
    url = "https://play.google.com/store/apps/details?id="
    r = requests.get(url + appid)
    time.sleep(random.random()*2)
    print("Checked {} returned {}".format(appid, r))
    return r
