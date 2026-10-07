# Source Generated with Decompyle++ (Python version)
# File: r9q_15_while_elif_else_return_sink.pyc (Python 3.11)

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
    else:
        return total
