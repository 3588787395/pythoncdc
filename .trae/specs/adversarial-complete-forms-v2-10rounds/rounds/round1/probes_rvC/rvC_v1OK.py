# Source Generated with Decompyle++ (Python version)
# File: rvC_v1.pyc (Python 3.11)

def sum_items(items, sink):
    total = 0
    try:
        for it in items:
            total += it
    finally:
        sink.append(total)
    return total
