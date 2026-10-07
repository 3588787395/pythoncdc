def r6_b117_a01_loopexit_run(items, other):
    total = 0
    for x in items:
        total += x
    head = list(other)
    lead = len(head) + total
    tags = tuple(lead)
    for y in tags:
        total += 1
    return total
