_LEDGER = {}

def s_b82a(key):
    try:
        return "miss"
    except KeyError:
        return _LEDGER[key]
    finally:
        if _LEDGER:
            _LEDGER.clear()
