# Source Generated with Decompyle++ (Python version)
# File: r10_04_import_try_cross.pyc (Python 3.11)

__doc__ = 'r10_04: import × try 四段交叉 + handler 内 as 别名'
def imp_try_sections(path):
    try:
        from m4 import opener
        fh = opener(path)
    except OSError as e:
        from m4 import fallback as fb
        fb(str(e))
        from m6 import closer
        closer(fh)
    else:
        from m5 import reader
        data = reader(fh)
    finally:
        from m6 import closer
        closer(fh)
    return data
def imp_alias_in_except(items):
    for it in items:
        try:
            if it > 0:
                from m7 import proc
                proc(it)
        except KeyError:
            from m7 import onmiss as om
            om(it)
        finally:
            if it < 0:
                from m8 import log
                log(it)
    return len(items)
