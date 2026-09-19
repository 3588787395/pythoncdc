# Source Generated with Decompyle++ (Python version)
# File: r2_04_return_in_loop_finally_dec.pyc (Python 3.11)

__doc__ = """Repro: get_user_info `return <value>` from a for-loop inside
try/finally.

CPython 3.11 compiles `return item` inside a for-loop (inside a
try whose finally is inlined on the return path) as:
    LOAD_FAST item      <- return value
    SWAP(2)             <- swap with the loop iterator
    POP_TOP             <- discard iterator
    <inlined finally: if fp is not None: fp.close()>
    RETURN_VALUE
The decompiler misparses this as a bare expression statement `item`
plus an if/else around the inlined close (`return fp.close()` /
`return None`), producing extra instructions and wrong semantics
(the function returns None instead of item).
"""
import csv
_app_log = print
def get_user_info(path, trade_id):
    fp = None
    try:
        fp = open(path, 'r')
        for item in csv.reader(fp):
            if item[0] == trade_id:
                if fp is not None:
                    fp.close()
                    if fp is not None:
                        return fp.close()
                    else:
                        return None
                elif fp is None:
                    break
                else:
                    fp.close()
                    return None
    except BaseException as x:
        _app_log.exception(x)
    finally:
        if fp is not None:
            fp.close()
