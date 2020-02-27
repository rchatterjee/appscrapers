from __future__ import print_function
"""Provides some functionalities for query filtering.  Moving everything related
to query filtering from other file (e.g., config.py) to this file.

"""
import re
import sys

# BLOCKING words
# Presence of these words immediately qualifies a
INCLUDING_WORDS = ['(track|cheat(ing)?).*(wife|girlfriend|spouse)', '(location|family|phone) tracker',
                   'gps', "location track(ing)?", 'cheat(s|ing) on', 'keylogger', 'anti.*theft']

# presence of these words immediately discard a search word
BLOCKING_WORDS = [ 'game', 'sport', 'mile', 'gta', 'xbox', 'royale', 'golf',
                   'fit', 'food', 'flight', 'run', 'tracks$', '\bcar\b', 'cheating '
                   'tom', 'cheat.*code', 'refund', 'cheatsheet', 'chart',
                   r'cheat.*sheet', r'cheat.*engine', '\bgas budd?y\b',
                   'calorie', 'money', 'expense', 'spending',
                   'tax', 'budget', 'period|diet|pregnancy|fertility', 'weight',
                   'gym', 'water', 'work ?out', 'track and field', 'exercise',
                   'cheats', r'baby.*photos', r'\btv\b',
                   r'time|hour|minute|day|month|year', 'sale', 'ski', 'sleep',
                   'walking', 'block', 'anti.*tracking', r'\Wrent', 'nutrition',
                   'corporate', r'insta(gram)?\W|facebook|twitter|tinder', 'spyfall', '\bforms?\b',
                   r'\b(dhl|fedex|ups)\b', 'read.*loud', 'quotes', r'ps(4|3)',
                   r'anti.*vi', 'windows', 'nod32', 'clam', 'security', '\Wmac','stickman'
]


def matched_string(regex):
    if not regex:
        return ""
    return regex.string[regex.start():regex.end()]

block_words = re.compile('|'.join(set(BLOCKING_WORDS)), re.I)
allowed_words = re.compile('|'.join(set(INCLUDING_WORDS)), re.I)

def remove_unrelated_apps(word):
    return block_words.search(word)

def extra_allowance(word):
    m = allowed_words.search(word)
    return m

def should_allow(query):
    """Returns a score (float) specifying what is the chance that we should
    consider this.  I am not putting any limit on the returned score but
    hopefully there will be some before I go too crazy.
    """
    m = remove_unrelated_apps(query)
    if m:
        print("Blocking {!r} :: {!r}".format(query, matched_string(m)),
              file=sys.stderr)
        m = extra_allowance(query)
        if m:
            print("-> Allowing {!r} :: {!r}".format(query, matched_string(m)),
                  file=sys.stderr)
            return 1
        return 0
    return 1  # If not filtered allow
