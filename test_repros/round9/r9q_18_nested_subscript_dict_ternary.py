def nested_subscript_ternary(df, c):
    if len(df) > 0:
        t = {}
        t['a'] = [df[0]]
        t['deep'] = {'k': [1 if c else 0]}
        return t
    return None
