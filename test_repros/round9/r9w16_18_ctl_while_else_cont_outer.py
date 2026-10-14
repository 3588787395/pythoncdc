def r9w16_18_ctl_while_else_cont_outer(rows, guard, log):
    for row in rows:
        while guard:
            guard = 0
        else:
            log(row)
            continue
        log(row)
