# Source Generated with Decompyle++ (Python version)
# File: e_while_tail.pyc (Python 3.11)

def e_while_tail(items, log):
    hit = 0
    while items:
        it = items.pop()
        if it < 0:
            break
        hit += it
    del items
    log.append(hit)
    return hit
