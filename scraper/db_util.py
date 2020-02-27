# ALL the funcitons above does not check for match in the db
# db related functions
import dataset
import json
from . import config
# import sys
import itertools
db = None
logger = config.setup_logger()


def _id_column_type():
    if db.__dict__.get('types'):
        return db.types.string
    else:
        return 'String'


def db_connect(test=True):
    global db
    if not db:
        db = dataset.connect(
            'sqlite:///{}'.format(
                config.TEST_DB_FILE if test else config.DB_FILE
            )
        )
    return db


def upsert(tab, data, check_cols, time_check=False):
    """
    Checks in the tab if data[check_cols] already exists, if so, then ignore,
    else, insert a new row with data. 
    """
    _where_str = ' and '.join("{0} = :{0}".format(col) for col in check_cols)
    _t = data.get('time', config.now()[:-5])
    _check = data.copy()

    if time_check:
        _where_str += " and time like :time"
        _check['time'] = _t + '%'

    try:
        res = list(tab.db.query(
            'select 1 from {table} where {where_str} limit 1'.format(
                table=tab.table.name,
                where_str=_where_str
            ), **_check
        ))
    except Exception as e:
        print("ERROR (upsert): >> {}".format(e))
        # raise Exception(e)
        res = []

    # list(tab.find(**{
    #     k: data[k]
    #     for k in check_cols
    # }))

    if not res:
        print("Inserting app -> {}".format(data.get(check_cols[0])))
        data['time'] = data.get('time', config.now())
        tab.insert(data)


def term_table_name(store):
    """Term tabel contains:
    term: the query term
    terms: closure of the term, obtained by calling the function
           check_closure_of_terms
    apps: the appids returned by get_appids for query, these are foreighn key
          of app_table
    """
    return store + "_terms"


def app_table_name(store):
    """Term tabel contains:
    appId: 
    contains lots of other important informations returned by appstores
    """
    return store + "_apps"


def reviews_table_name(store):
    """Term tabel contains:
    id: primary id (an id provided by the store)
    contains (appId and one comment per row)
    """
    return store + "_reviews"


def desc_table_name(store):
    """Description table contains, 
    appId (primary_id), desc (text), date (today's date)
    """
    return store + "_desc"


def exists(table, colname, value, time_check=False):
    """Checks if a @value exists in a column @colname in the table @tablename.
    """
    _t=config.now()[:-5]
    timecheck_str = "and time like :time" if time_check else ''    
    if isinstance(table, str):
        table = db_connect().get_table(table)
    try:
        ret = list(table.db.query(
            "select 1 from {tabname} where {colname}= :value "\
            "COLLATE NOCASE {timestr} "\
            "limit 1"\
                .format(colname=colname,
                        tabname=table.table.name,
                        timestr=timecheck_str
                ), value=value, time=_t
        ))
        if ret:
            return True
    except Exception as e:
        # print("exists >> ", e, file=sys.stderr)
        logger.exception("exists >> {}".format(e))
        return False
    return False

def _get_all(table, col):
    """
    Returns all col values from table
    """
    if isinstance(table, str):
        table = db_connect().get_table(table)
    q = 'select {} from {}'.format(col, table.table.name)
    return [r[col] for r in table.db.query(q)]

def _get_all_LANG_COUNTRY(table, col):
    """
    Returns all col values from table for particular language and country pair
    """
    if isinstance(table, str):
        table = db_connect().get_table(table)
    q = 'select {} from {} where LANG==\'{}\' and COUNTRY==\'{}\''.format(col, table.table.name, config.LANG, config.COUNTRY)
    return [r[col] for r in table.db.query(q)]

def get_all_appids(store, test):
    """
    Return all the appids found so far in search
    which is the superset of all the apps stored in the android_terms
    """
    table = term_table_name(store)
    try:
        return set(itertools.chain(*(json.loads(a) for a in _get_all_LANG_COUNTRY(table, 'apps')))) 
    except Exception  as e:
        # print(e, file=sys.stderr)
        logger.exception(">> get_all_appids", e)
        return set()
        

def get_all_terms(store):
    """
    Return all terms
    """
    table = term_table_name(store)
    try:
        return _get_all_LANG_COUNTRY(table, 'term')
    except Exception as e:
        # print(e, file=sys.stderr)
        logger.exception("get_all_terms >> ", e)
        return []

def get_all_terms_LANG_COUNTRY(store):
    """
    Return all terms
    """
    table = term_table_name(store)
    try:
        return _get_all_LANG_COUNTRY(table, 'term')
    except Exception as e:
        # print(e, file=sys.stderr)
        logger.exception("get_all_terms >> ", e)
        return []


