# Source Generated with Decompyle++ (Python version)
# File: rec1_synth_b87c.pyc (Python 3.11)

def s_b87c(rows):
    out = []
    try:
        for r in rows:
            try:
                for c in r:
                    out.append(c)
            finally:
                out.append(None)
    except ValueError:
        return []
    return out
