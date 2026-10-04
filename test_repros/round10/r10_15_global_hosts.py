"""r10_15: global × 深层宿主交叉（try/with/match/for>if，深度 ≥3）"""
LOG = []
CACHE = {}


def g_in_try_except(key):
    try:
        global CACHE
        if key not in CACHE:
            CACHE[key] = key * 2
        return CACHE[key]
    except TypeError:
        return None
    finally:
        if CACHE:
            global LOG
            LOG.append(key)


def g_in_with(path):
    with open(path) as fh:
        global LOG
        for line in fh:
            if "err" in line:
                LOG.append(line)
    return len(LOG)


def g_in_match(v):
    global CACHE
    match v:
        case int(n) if n > 0:
            CACHE[v] = n
        case [x, *rest]:
            if rest:
                CACHE["seq"] = len(rest)
        case _:
            CACHE.setdefault("d", 0)
    return CACHE


def g_in_for_if(rows):
    def run():
        global LOG
        for r in rows:
            if r > 0:
                LOG.append(r)
        return LOG
    return run()
