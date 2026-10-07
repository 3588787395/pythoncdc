# Source Generated with Decompyle++ (Python version)
# File: r9q_19_subscript_listcomp_assign.pyc (Python 3.11)

def subscript_listcomp(df):
    if len(df) > 0:
        t = {}
        t['a'] = [df[0]]
        t['z'] = [v for v in df if v != 0]
        return t
    else:
        return None
