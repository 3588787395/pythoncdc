def while_bare_break(limit, exit_val):
    count = 0
    while count < limit:
        if count == exit_val:
            break
        count += 1
    else:
        count = -1
    return count
