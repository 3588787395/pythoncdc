# Source Generated with Decompyle++ (Python version)
# File: rec1_synth_b69b.pyc (Python 3.11)

def s_b69b(a, items):
    if a:
        try:
            items.append(a)
        finally:
            items.reverse()
        return items
    else:
        return []
