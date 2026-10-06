# Source Generated with Decompyle++ (Python version)
# File: r2v3_c11_inside_while_or_not_operand.pyc (Python 3.11)

def f(q, uinfo):
    while q:
        username = q.pop()
        if not (username not in uinfo or uinfo[username]):
            continue
            use(username)
