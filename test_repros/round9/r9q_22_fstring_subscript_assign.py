def fstring_subscript_assign(df, x):
    if len(df) > 0:
        t = {}
        t['a'] = [df[0]]
        t['msg'] = f'v={x}'
        return t
    return None
