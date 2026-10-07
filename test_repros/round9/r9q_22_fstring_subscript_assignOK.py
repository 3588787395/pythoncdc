# Source Generated with Decompyle++ (Python version)
# File: r9q_22_fstring_subscript_assign.pyc (Python 3.11)

def fstring_subscript_assign(df, x):
    if len(df) > 0:
        t = {}
        t['a'] = [df[0]]
        t['msg'] = f'v={x}'
        return t
    else:
        return None
