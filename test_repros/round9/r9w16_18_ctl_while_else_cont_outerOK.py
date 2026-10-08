# Source Generated with Decompyle++ (Python version)
# File: r9w16_18_ctl_while_else_cont_outer.pyc (Python 3.11)

def r9w16_18_ctl_while_else_cont_outer(rows, guard, log):
    for row in rows:
        while guard:
            guard = 0
        log(row)
