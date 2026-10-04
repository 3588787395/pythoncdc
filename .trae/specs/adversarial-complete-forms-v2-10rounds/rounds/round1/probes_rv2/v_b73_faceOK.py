# Source Generated with Decompyle++ (Python version)
# File: v_b73_face.pyc (Python 3.11)

__doc__ = 'rv2 变体面 B73（r10_04 imp_try_sections 邻域）：finally 条件段外推 / 无 finally 负对照'
def v_imp_cond_fin(path):
    try:
        from m4 import opener
        fh = opener(path)
    except OSError as e:
        from m4 import fallback as fb
        fb(str(e))
        from m6 import closer
        if fh:
            return closer(fh)
        else:
            return None
    else:
        from m5 import reader
        data = reader(fh)
    finally:
        from m6 import closer
        if fh:
            closer(fh)
    return data
def n_imp_nofin(path):
    try:
        from m4 import opener
        return opener(path)
    except OSError as e:
        from m4 import fallback as fb
        return fb(str(e))
