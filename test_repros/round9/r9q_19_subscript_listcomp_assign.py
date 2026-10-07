def subscript_listcomp(df):
    if len(df) > 0:
        t = {}
        t['a'] = [df[0]]
        t['z'] = [v for v in df if v != 0]
        return t
    return None
