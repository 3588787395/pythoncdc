# Source Generated with Decompyle++ (Python version)
# File: rec1_synth_b82a.pyc (Python 3.11)

_LEDGER = {}
def s_b82a(key):
    try:
        return 'miss'
    except KeyError:
        return _LEDGER[key]
    finally:
        if _LEDGER:
            _LEDGER.clear()
