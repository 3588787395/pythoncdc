# Source Generated with Decompyle++ (Python version)
# File: rec1_synth_b82b.pyc (Python 3.11)

_STATS = {'n': 0}
def s_b82b(key):
    try:
        return 'absent'
    except LookupError:
        return _STATS.get(key)
    finally:
        if _STATS:
            _STATS['n'] += 1
