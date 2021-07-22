#!/usr/bin/env python3
from __future__ import print_function


"""
This file is used to download all the app-meta data from Play Store and App
store.  First, most exciting functionality that it provides is to compute
query-snowballing: Starting from a small set of queries this expands that set to
a set based on Play Store query completion api.

It also provides similar options for iTunes App Store. 
"""



import os
import sys
import dataset
import json
import copy
from collections import Counter
from scraper import config, queries
from scraper.query_filter import should_allow
import argparse
from scraper.appstore_api import get_store_func, app_page, connect
from scraper.db_util import (
    db_connect, upsert, term_table_name, app_table_name, reviews_table_name,
    desc_table_name, exists, get_all_appids, _id_column_type, get_all_terms,
    get_all_terms_LANG_COUNTRY
)
from scraper.search_engines import get_term_expansion
from scraper.appdetails import download_app_details, download_reviews, get_similar_apps
from collections import OrderedDict, deque
from dateutil import parser as dateparser
import pandas as pd

logger = config.setup_logger()
missed_items_file = open('missed_items', 'a')


def get_operation_closure(op_func, start_nodes, limit=1000, black_list=None):
    """
    Given a similarity function op_func and a start point start_node, returns
    the closure of the start_node. By closure I meant, a set which is closed
    under the operation op_func and contains start_node.
    :return: Retunrs closure and the level information
    """
    if not isinstance(start_nodes, (list, set)):
        start_nodes = [start_nodes]
    parent = ''
    unchecked = {n: parent for n in start_nodes}
    _unchecked_list = deque(unchecked.keys())
    closure = {n: parent for n in start_nodes}
    while _unchecked_list and len(closure) < limit:
        node = _unchecked_list.popleft()
        parent = unchecked[node]
        if black_list and black_list(node):
            logger.info("Filtered query: {!r}".format(node))
            continue
        for n in op_func(node):
            if n not in unchecked:
                unchecked[n] = node  # node is the parent of n
                _unchecked_list.append(n)
                closure[n] = closure.get(n, node)
            # unchecked.update({n: level+1 for n in set(op_func(node))
            #                   if n not in closure and n not in unchecked})
        if len(closure) % 10 == 0:
            logger.info("Done={:3d},\t\tremaining={:3d}"
                  .format(len(closure), len(_unchecked_list)))
    if len(closure) >= limit:
        logger.info("Hit the maximum allowed limit of calls!!"
              "len(closure)={}\nUnchecked ({}): {}".format(
                  len(closure), 
                  len(_unchecked_list), 
                  _unchecked_list)
        )
    return closure


def get_term_completions(term, store):
    """
    Get term completion suggestions for a term
    """
    if store == 'android':
        _t_suggest_func = get_store_func('suggest', store)
        suggest = _t_suggest_func
    elif store == 'ios':
        # Ios provides a priority score based on searchs, we are not
        # recording it right now.  A priority index is also returned which
        # goes from 0 for terms with low traffic to 10000 for the most
        # searched terms.
        _t_suggest_func = get_store_func('suggest', store)
        suggest = lambda d: [t['term'] for t in _t_suggest_func(d)]
    elif store.startswith('google') or store.startswith('bing'):
        return get_term_expansion(term, store)
    else:
        raise Exception("Not allowed for store: {}".format(store))
    return suggest({'term': term, 'lang':config.LANG, 'country':config.COUNTRY, 'throttle': config.THROTTLE_DEFAULT})



def get_closure_of_terms(terms, store, limit=1000, savejson=False):
    """
    Returns a set of terms that is the smallest closure with respect to
    the similarity metric including the given @terms. Build snow-ball starting
    from @terms

    @terms: list of terms (must be iterable)
    @store: 'android' or 'ios'
    @limit: When to stop if the closure gets too big
    """
    _term_completions = lambda t: get_term_completions(t, store)
    terms_sugg_dict = get_operation_closure(
        _term_completions, terms, limit=limit,
        black_list=lambda x: should_allow(x) < 0.5
    )
    if savejson:
        outfname = 'data/query_closure_{}_{}.json'.format(store, limit)
        with open(outfname, 'w') as f:
            json.dump(terms_sugg_dict, f, indent=4)

    return terms_sugg_dict



def get_closure_of_apps(appids, store, limit=100):
    assert store in ('android', 'ios'), \
        "Other stores ({!r}) not supported".format(store)
    if not isinstance(appids, (list, set)):
        appids = [appids]
    return get_operation_closure(
        lambda x: get_similar_apps(x, store, limit=10),
        appids, limit=limit
    )


def get_appids_for_query(query, store):
    """For a query, return top 10 apps returned by the store"""
    search = get_store_func('search', store)
    ret = set(
        a['appId']
        for a in search({
            'term': query,
            'num': config.APPS_PER_QUERY,
            'throttle': config.THROTTLE_DEFAULT,
            'lang': config.LANG,
            'country': config.COUNTRY,
            'fullDetail': False,
            'price': 'all'
        })
    )
    return ret




def get_terms_and_apps_for_term(term, store, force=False, limit=1000):
    """A wrapper over the term databse. returns the terms and apps.
    return type= dict: {'terms': [], 'apps': []}
    
    """
    term = term
    db = db_connect()
    table = db.get_table(term_table_name(store))

    ret = None
    serialize_keys = ['terms', 'apps']
    if exists(table, 'term', term, time_check=force):  # Get from DB
        ret = list(db.query(
            'select terms,apps from {0} where term="{1}" COLLATE NOCASE limit 1'
                .format(table.table.name, term)))[0]
        for k in serialize_keys:
            if k in ret and len(ret[k]) > 0:
                try:
                    ret[k] = json.loads(ret[k])
                except Exception as e:
                    logger("get_terms_and_apps_for_term >> ", store, e, ret[k],
                          file=sys.stderr)
                    return get_terms_and_apps_for_term(term, store,
                                                       force=True, limit=limit)
    else:
        ret = {
            'terms': get_closure_of_terms(
                terms=[term],
                store=store, limit=limit),
            'apps': [x
                     for x in get_appids_for_query(term, store=store)],
            'term': term,
            'time': config.now(),
            'lang': config.LANG,
            'country': config.COUNTRY,
        }
        ins_ret = copy.deepcopy(ret)
        for k in serialize_keys:
            if k in ret:
                ins_ret[k] = json.dumps(ret[k])
        upsert(table, ins_ret, ['term', 'terms', 'apps']) 
    return ret



def update_desc_table(ret, store):
    """Updates the desc table with the new description for the app in @ret
    """
    db = db_connect()
    table = db.get_table(
        desc_table_name(store)
    )
    desc = ret['description']
    last_desc_sql = "select description from {0} where appId='{1}' and " \
                    "time=(select MAX(time) from {0} where appId='{1}')".format(table.table.name, ret['appId'])
    last_desc = ''
    try:
        if 'description' in table.columns:
            _l_last_desc = list(db.query(last_desc_sql))
            if _l_last_desc:
                last_desc = _l_last_desc[0]['description']
        if last_desc != desc:
            table.insert({
                'appId': ret['appId'],
                'time': config.now(),
                'description': ret['description']
        })
    except Exception as e:
        logger.error("Exception.update_desc_table!!", e)






# ---------------- Script Running function --------------------------
def download_all_reviews(store):
    """Download reviews for each app in the database
    """
    db = db_connect()
    apps = (r['appId'] for r in db.query('select appId from android_apps'))
    for appid in apps:
        download_reviews(appid, store=store, limit=
                         config.NUM_COMMENTS_TO_DOWNLOAD)


def isactive(appid, store):
    """
    Checks if an app is still active
    """
    assert store == 'android', 'Does not support other stores' 
    def is_ok(r):
        return 1 if r.ok else 0 if r.status_code == 404 else -1
    if not appid.islower():
        return is_ok(app_page(appid))

    r = 0
    for a in get_appids_for_query(appid, store='android'):
        if a.lower() == appid.lower():
            r = app_page(a)
            if r != -1: return r
    return r


def download_app_details_all(store, reviews_too=False, test=False, force=False):
    """
    Download all the terms and apps for them and store in the databse
    """
    db = db_connect(test=test)
    apps_done = set()
    all_appids = get_all_appids(store, test)
    logger.debug("Got all appids: {}".format(len(all_appids)))
    for i, appid in enumerate(all_appids):
        if appid not in apps_done:
            apps_done.add(appid)
            # download app details
            download_app_details(appid, store=store, force=True)
            # print("Downloaded {}. {}".format(i, appid))
        if i % 10 == 0:
            logger.info("Done downloading apps ({}): {}".format(store, i))
    logger.info("Downloading reviews ({}).. #Apps: {}".format(store, len(apps_done)))
    # download reviews
    if reviews_too:
        for appid in apps_done:
            download_reviews(appid, store=store,
                             limit=config.NUM_COMMENTS_TO_DOWNLOAD)


def download_all_terms_appids(store, test=False, force=False):
    """Download the appids and terms by search for the terms given in config. 
    It computes the closure of the terms, before starting.

    """
    db = db_connect(test=test)
    terms = queries.seed_queries(store)

    # Save all the configs
    config_tab = db.get_table('configs')
    config_tab.insert_many(
        {'key': k, 'value': json.dumps(v), 'time': config.now()}
        for k,v in vars(config).items()
        if k.isupper() and not k.endswith('_DIR')
    )

    config_tab.insert({'key': 'store', 'value': store, 'time': config.now()})

    closure_of_queries = get_closure_of_terms(terms, store=store, savejson=True)
    config_tab.insert({
        'key': 'snowball',
        'value': json.dumps(closure_of_queries),
        'time': config.now()
    })
    
    all_queries = set(get_all_terms_LANG_COUNTRY(store)) | set(closure_of_queries)
    if store == 'ios': # ios term suggestions are bad, hence utilize the android terms here. 
        all_queries |= set(x for x,y in Counter(get_all_terms_LANG_COUNTRY('android')).most_common(1000))

    print("download_all_terms >> {} Term set size: {}"
          .format(store, len(all_queries)))
    print("download_all_apps.1 >> {} >> {}".format(store, str(all_queries)))
    for i, term in enumerate(all_queries):
        if i % 10 == 0:
            print("download_all_terms.3 >> Done {} terms".format(i))
            db.commit()
            config.sleep_time(1)  # I don't want to get blocked.
        # download terms, appids, and store
        ret = get_terms_and_apps_for_term(term, store=store, limit=1000, force=True)
        tterms, apps = ret['terms'], ret['apps']
        tterms = set(tterms)
        if not tterms.issubset(all_queries):
            print("download_all_terms.2 >> Missed for {!r}: {!r}\n" \
                  .format(term, list(set(tterms) - all_queries)),
                  file=missed_items_file
            )
            # raise Exception("download_all_apps.2 >> Missed:",
            # tterms-all_queries)
        print(ret)


def download_main(**kwargs):
    logger.info("1. Downloading the terms first. ({})".format(kwargs.get('store')))
    download_all_terms_appids(
        store=kwargs.get('store'), test=kwargs.get('test'), force=kwargs.get('force')
    )
    logger.info("Finished downloading the terms. Exiting for test.")

    logger.info("2. Downloading the app details.")
    download_app_details_all(
        store=kwargs.get('store'), test=kwargs.get('test'), force=kwargs.get('force'),
        reviews_too=kwargs.get('reviews_too')
    )

    logger.info("3. Downloading the app reviews.")
    logger.info("TODO")
    # download_app_details(
    #     store=kwargs.get('store'), test=kwargs.get('test'), force=kwargs.get('force'),
    #     reviews_too=kwargs.get('reviews_too')
    # )


class NewJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (set)):
            return list(obj)
        else:
            return json.JSONEncoder.default(obj)


def test_functions(store):
    assert store in ('android', 'ios')
    appid = 'com.mojang.minecraftpe' if store == 'android' \
        else 'com.nerdyoctopus.dots'
    # closure_terms = list(get_closure_of_terms(['spy'], store=store))
    # ret = get_app_details('privatealbum', store=store)
    ret = download_reviews(appid, store=store, limit=41)
    # closure_terms = list(get_closure_of_apps(['com.mojang.minecraftpe'],
    #                                          store='android'))
    # closure_terms = list(get_closure_of_apps(['com.nerdyoctopus.dots'],
    #                                          store='ios', limit=20))
    # closure_terms = get_terms_and_apps_for_term('candy', store='ios', 
    #                                             limit=200)
    # closure_terms = get_appids_for_query('candy')
    # import json
    logger.info("test_functions >> ", len(ret),
                json.dumps(ret, indent=4, cls=NewJSONEncoder))


def arguments():
    """
    Set up argument parser
    """
    parser = argparse.ArgumentParser(
        description="A scraping tool to perform query snowballing, "
                    "downloading metadata from Play Store and iTuenes App store.",
        fromfile_prefix_chars='@'
    )
    parser.add_argument("--appstore",
                        help="Which app store to target. **Options: android, ios**. "\
                        "'google-realted' and 'google-comp' are not supported from commandline.",
                        action="store", choices=['android', 'ios', 'google-related',
                                                 'google-comp', 'bing'],
                        )
    parser.add_argument("--reviews",
                        help="Download comments. Only valid if"
                             "--download flag is given", action="store_true",
                        default=False)
    parser.add_argument("--apps", nargs='+', help="List of appIds to download",
                        action="store", default=['com.mojang.minecraftpe'])
    parser.add_argument("--appdetails", dest='action', help="Action: download app(s).",
                        action="store_const", const="appdetails")
    parser.add_argument("--crawl", dest='action', help="Start crawling. Start fresh. Run it everyday at 10am EST.",
                        action="store_const", const="crawl")
    parser.add_argument("--test", dest="action", help="Run test",
                        action="store_const", const="test")
    parser.add_argument('--qs', dest="action",
                        help="Perform query snowballing on the app store",
                        action="store_const", const="qs")
    parser.add_argument('--fresh', action="store_true", default=False,
                        help="Start the node server server.js so that we are not hitting the same cache")
    parser.add_argument('--prod', action="store_true", default=False,
                        help="Stores in databse only if this is true")
    parser.add_argument('--search', action="store", default='', help="Search apps with this query")
    parser.add_argument('--similarapps', action="store_const", dest="action", const="similarapps",
                        help="Get closure of apps of the given appIds in --apps")
    return parser


if __name__ == "__main__":
    parser = arguments()
    args = parser.parse_args()
    print(args)
    logger.info(args)
    store = args.appstore
    if not store:
        print("appstore cannot be {!r}".format(store))
        exit(-1)
    if args.fresh:
        connect(store, fresh=True)
    apps = []
    if args.apps:
        if os.path.exists(args.apps[0]):
            apps = [l.strip() for l in open(args.apps[0])]
            if os.path.exists('{}_done'.format(args.apps[0])):
                d = pd.read_csv('{}_done'.format(args.apps[0]))
                apps = set(apps) - set(d.appId)
        else:
            apps = args.apps        

    if args.action == 'crawl':
        # connect(fresh=True)
        download_main(
            store=store, force=False,
            test=not args.prod, reviews_too=args.reviews
        )
    elif args.action == 'test':
        logger.info("Running simple test scripts!")
        test_functions(store)
    elif args.search:
        logger.info(get_appids_for_query(args.search, store=store))
    elif args.action == 'appdetails':
        db = db_connect(test=not args.prod)
        print("# of apps to download: {}".format(len(apps)))
        for appid in apps:
            appid = appid.strip()
            logger.info("Downloading %s", appid)
            # print(appid,
            #       json.dumps(get_app_details(appid, store), indent=4))
            download_app_details(appid, store=store)
            if args.reviews:
                download_reviews(appid, store=store,
                                 limit=config.NUM_COMMENTS_TO_DOWNLOAD)

    elif args.reviews:
        db = db_connect(test=not args.prod)
        print("# of apps to download: {}".format(len(apps)))
        for i, appid in enumerate(apps):
            appid = appid.strip()
            logger.info("%4d. Downloading %s", i, appid)
            download_reviews(
                appid, store=store, limit=config.NUM_COMMENTS_TO_DOWNLOAD
            )

    elif args.action == 'qs':
        if args.apps[0] == 'all':
            seed = config.seed_queries(store)
        else:
            seed = args.apps
        print("Snowball of {}".format(seed))
        print(seed, store)
        print(get_closure_of_terms(seed, store, limit=10000))
    elif args.action == 'similarapps':
        print("Similar apps of {}".format(args.apps))
        print(get_closure_of_apps(args.apps, store, limit=100))
    else:
        parser.print_help()
