_STATS = {"n": 0}

def s_b82b(key):
    try:
        return "absent"
    except LookupError:
        return _STATS.get(key)
    finally:
        if _STATS:
            _STATS["n"] += 1
