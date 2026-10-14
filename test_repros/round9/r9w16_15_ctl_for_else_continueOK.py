# Source Generated with Decompyle++ (Python version)
# File: r9w16_15_ctl_for_else_continue.pyc (Python 3.11)

def r9w16_15_ctl_for_else_continue(rows, log):
    for row in rows:
        for col in row:
            if col.hit:
                break
        else:
            continue
        log(row)
