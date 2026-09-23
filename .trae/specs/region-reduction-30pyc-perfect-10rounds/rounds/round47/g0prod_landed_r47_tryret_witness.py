# Source Generated with Decompyle++ (Python version)
# File: g0_landed_r47_tryret_witness.pyc (Python 3.11)

__doc__ = """Round 47 G0 witnesses: `return <expr>` as the last statement of a try body.

Real target: site-packages/fly/data/quote_handler.pyc :: <module>.get_Ashares_local
  ORIG   : STORE_FAST returnlist / LOAD_FAST returnlist / RETURN_VALUE
  LANDED : STORE_FAST returnlist / LOAD_FAST returnlist / POP_TOP / LOAD_CONST None
           / RETURN_VALUE        ==> product reads `returnlist` + `return None`
"""
def r47_01_try_tail_return(date=None):
    returnlist = []
    try:
        if date is None:
            date = time.strftime('%Y%m%d')
        else:
            date = str(date)
        rows = pandas.read_csv(path)
        returnlist = [i for i in rows]
        returnlist
        return None
    except BaseException as e:
        system_log.error(str(e))
        raise e
def r47_02_try_tail_bare_return(date=None):
    returnlist = []
    try:
        if date is None:
            date = time.strftime('%Y%m%d')
        rows = pandas.read_csv(path)
        returnlist = [i for i in rows]
        return None
    except BaseException as e:
        system_log.error(str(e))
        raise e
def r47_03_no_try_tail_return(date=None):
    returnlist = []
    if date is None:
        date = time.strftime('%Y%m%d')
    rows = pandas.read_csv(path)
    returnlist = [i for i in rows]
    return returnlist
def r47_04_try_tail_return_call(date=None):
    returnlist = []
    try:
        if date is None:
            date = time.strftime('%Y%m%d')
        rows = pandas.read_csv(path)
        returnlist = [i for i in rows]
        len(returnlist)
        return None
    except BaseException as e:
        system_log.error(str(e))
        raise e
def r47_05_try_except_noreraise(date=None):
    returnlist = []
    try:
        if date is None:
            date = time.strftime('%Y%m%d')
        rows = pandas.read_csv(path)
        returnlist = [i for i in rows]
        returnlist
        return None
    except BaseException as e:
        system_log.error(str(e))
        return None
def r47_06_try_mid_return_tail_nothing(date=None):
    returnlist = []
    try:
        if date is None:
            return returnlist
        rows = pandas.read_csv(path)
        returnlist = [i for i in rows]
    except BaseException as e:
        system_log.error(str(e))
        raise e
    return returnlist
def r47_07_try_tail_return_attr(date=None):
    obj = something()
    try:
        if date is None:
            date = time.strftime('%Y%m%d')
        rows = pandas.read_csv(path)
        obj.rows = rows
        return obj.rows
        return None
    except BaseException as e:
        system_log.error(str(e))
        raise e
def r47_08_try_tail_return_const(date=None):
    total = 0
    try:
        if date is None:
            date = time.strftime('%Y%m%d')
        rows = pandas.read_csv(path)
        total = len(rows)
        return 7
    except BaseException as e:
        system_log.error(str(e))
        raise e
