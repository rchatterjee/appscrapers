#!/usr/bin/env python3

import pandas as pd
import os
import sys
from lxml import html
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import json
from collections import Counter
import pandas as pd

QUERY_RELEVANCE = None

def isrelevant(fname):
    """Is the fname / quety relevant"""
    global QUERY_RELEVANCE
    if not QUERY_RELEVANCE:
        _t = pd.read_csv('gqueries.relevant.csv')
        QUERY_RELEVANCE = dict(zip(_t.term.tolist(), _t.relevant.tolist()))
    return QUERY_RELEVANCE.get(
        ' '.join(fname.rsplit('.', 1)[0].split('_')),
        'n') == 'y'

def parse_url(url):
    """
    Parse out the url pointed by google
    '/url?q=http://www.logsat.com/iPhone/familytracker/&sa=U&ved=0ahUKEwiakOr-_MjWAhXIq1QKHXQ4CbgQFggLMAA&usg=AFQjCNGmnn_OcB0ybSvF5bPgV8iWS99peg'
    """
    return parse_qs(urlparse(url).query).get('q', [url])[0]

def parse_page(page_f):
    """Given a html_file name extract all the links in the page and all the query
    suggestions.
    """
    def parse_link(e):
        a = e.xpath('.//a')
        if not a: return '[no-url]'
        return parse_url(a[0].attrib.get('href'))

    tree = html.parse(page_f)
    links = [
        (e.text_content(), parse_link(e))
        for e in 
        # tree.xpath('//*[@id="ires"]/ol/div//h3/a')
        tree.xpath('//*[@class="r"]')
    ]
    suggestions = [
        e.text_content() for e in 
        # tree.xpath('//*[@id="center_col"]/div//table/tbody/tr//td//p/a')
        tree.xpath('//p')  # A dirty hack, but works for now
    ]

    # TODO - Ads
    ads = [
        (
            e.text_content(), 
            e.xpath('.//*[@class="ads-visurl"]/cite')[0].text_content()
        )
        for e in
        # tree.xpath('//*[@class="ads-visurl"]/cite')
        tree.xpath('//*[@class="ads-ad"]')
    ]
    return links, suggestions, ads


def collect_all_pages(dirname):
    """Main function to parse all the pages in the selenium_firefox_windows and
    selenium_firefox_android folder.
    TODO: The xpaths might be different for android and windows. 

    Stores the links, suggestions and ads in `parsed_@dirname.json` file. 
    """
    D = {}
    for i, fpath in enumerate(Path(dirname).glob('**/*.html')):
        # if not isrelevant(fpath.name): continue
        print(i, fpath)
        links, suggestions, ads = parse_page(fpath.open())
        D[fpath.name.rsplit('.', 1)[0]] = {
            'links': links,
            'suggestions': suggestions,
            'ads': ads
        }

    with open('parsed_{}.json'.format(Path(dirname).name), 'w') as f:
        json.dump(D, f, indent=2);


def prune_lists(json_db):
    """Read the json file created by collect_all_pages function and prune the lists
    based on some heuristics, then, get the pages and look for android in them. 
    Finally, manually check the html pages for names of android apps used for spying.  
    """
    blacklisted_domains = {
        'm.youtube.com', 'youtube.com',
        'play.google.com',
        'itunes.apple.com',
        'community.sprint.com', 
        'www.wri.org'
    }
    d = json.load(open(json_db))
    df = pd.Data
    pass


if __name__ == "__main__":
    if os.path.isdir(sys.argv[1]):
        collect_all_pages(sys.argv[1])
    else:
         print(json.dumps(parse_page(open(sys.argv[1])), indent=4))
