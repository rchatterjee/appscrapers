"""
I plan to put query suggestion functions for different engines in this file
so that we can try different search engine features and see how to get a
better search expansion
"""
import requests
from lxml import html
import time, random
from scraper.query_filter import should_allow
from joblib import Memory
import io
from scraper.parse_google import parse_page

HL = 'en'
CR = 'US'
testing = True

memory = Memory(
    cachedir='./data/cache' if not testing else None,
    verbose=0,
    compress=8,
    bytes_limit=int(2**31)  # 2 GB limit
)

def _filter_list(l):
    return [x for x in l if len(x)>3 and should_allow(x) > 0.5]

# Bing
BING_API = "http://api.bing.com/osjson.aspx?query="
@memory.cache(ignore=['filter_list'])
def bing_suggest(q, filter_list=_filter_list):
    r = requests.get(BING_API + q.replace(' ', '+'))
    if not r.ok:
        print("ERROR: Search failed for {} in Bing".format(q))
        return []
    else:
        return filter_list(r.json()[0])

# Google
GOOGLE_RELATED_QUERY_API = "https://www.google.com/search?source=hp&q={q}&hl={hl}&cr=country{cr}"
UA = {
    # 'user-agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"
    'user-agent': "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.97 Safari/537.11",
    'accept-encoding': "compress, gzip"
}
@memory.cache(ignore=['filter_list'])
def google_suggest(q, filter_list=_filter_list):
    """
    parses the google search pages. 
    """
    url = GOOGLE_RELATED_QUERY_API.format(q='+'.join(q.split()), hl=HL, cr=CR)
    print(url)
    try:
        r = requests.get(url, headers=UA, timeout=2)
        tree = html.fromstring(r.content)
        assert r.ok, "Return code from google: {}".format(r.status_code)
        time.sleep(random.random())
        return filter_list([
            e.text_content() for e in 
            tree.xpath('//p//a')
        ])
    except Exception as ex:
        print("Exception: {}".format(ex))
        print("ERROR: Failed for q={} in Google".format(q))
        if r.status_code == 503:
            print("Extra sleep")
            time.sleep(60)  # Wait a minute.
        return []


# Google Search
GOOGLE_SEARCH_QUERY = "https://www.google.com/search?source=hp&num=30&start=0&q={q}"
@memory.cache()
def google_search(q, n=30, site=None):
    """
    Return the top @n google search results for the query q, 
    and returns the search suggetions 
    """
    if site:
        q = 'site:{} {}'.format(site, q)
    url = GOOGLE_SEARCH_QUERY.format(q='+'.join(q.split()))
    try:
        r = requests.get(url, headers=UA, timeout=2)
        tree = html.fromstring(r.content)
        assert r.ok, "Return code from google: {}".format(r.status_code)
        time.sleep(random.random())
        links, suggestions, ads = parse_page(io.BytesIO(r.content))

    except Exception as ex:
        print("Exception: {}".format(ex))
        print("ERROR: Failed for q={} in Google".format(q))
        if r.status_code == 503:
            print("Extra sleep")
            time.sleep(60)  # Wait a minute.
        links, suggestions, ads = [], [], []
    return {
        'links': links,
        'suggestions': _filter_list(suggestions),
        'ads': ads
    }



GOOGLE_COMPLETION_QUERY_API = "http://suggestqueries.google.com/complete/search?q={}&client=firefox&hl={hl}&cr=country{cr}"
@memory.cache(ignore=['filter_list'])
def google_complete(q, filter_list=_filter_list):
    """
    Uses google query completion API
    """
    q = q.replace(' ', '+')
    url = GOOGLE_COMPLETION_QUERY_API.format(q=q, hl=HL, cr=CR)
    r = requests.get(url)
    if not r.ok:
        print("ERROR: Search Failed for {} in Google completion".format(q))
        return []
    # Make sure google does not get angry with us
    time.sleep(random.random())
    try:
        rq, rd = r.json()
        return filter_list(rd)
    except Exception as e:
        print("Exception:::", e, r.text)
        return []

# Yahoo


# Google Play completion api
PLAY_STORE_API="https://market.android.com/suggest/SuggRequest?json=1&c=3&query={}&hl=en&gl=US".format
@memory.cache(ignore=['filter_list'])
def play_store_complete(q, filter_list=_filter_list):
    """
    Use google play scraper
    """
    url = PLAY_STORE_API(q)
    r = requests.get(url)
    if not r.ok:
        print("ERROR: Search Failed for {} in Play Store completion".format(q))
        return []
    # Make sure google does not get angry with us
    try:
        return filter_list([rd['s'] for rd in r.json()])
    except Exception as e:
        print("Exception:::", e, r.text)
        return []
    finally:
        time.sleep(random.random()) 


def get_term_expansion(term, store):
    """
    expand terms based on the store
    """
    assert store in ('google-related', 'google-comp', 'bing', 'android'), \
        "store={} not supported".format(store)

    return {
        'google-related': google_suggest,
        'google-comp': google_complete,
        'bing': bing_suggest,
        'android': play_store_complete
    }[store](term)


if __name__ == "__main__":
    import sys
    if len(sys.argv)>3:
        HL = sys.argv[1]
        CR = sys.argv[2]
        q = sys.argv[3]
        print(google_suggest(q))
    elif len(sys.argv) == 1:
        q = sys.argv[1]
        print(google_suggest(q))
    else:
        print("""
$ python scraper.search_engines <language> <country> <query>
# Or, default language=US, country=EN
$ python scraper.search_engines <query>
# E.g.,
$ python scraper.search_engines "Amy I being tracked"
$ python scraper.search_engines bn bn "আমাকে কি track করা হচ্ছে"
""")
    
