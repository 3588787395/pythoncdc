def while_elif_else_sink(items, lg):
    total = 0
    for it in items:
        if it == 1:
            total += it
        elif it == 2:
            lg.warn('skip')
            continue
        else:
            return None
        lg.info(total)
    return total
