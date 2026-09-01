# R101-Pattern-D: unreachable second return after a return inside try
# (get_market_detail_online shape); HEAD-era output kept both returns,
# current output drops the unreachable one and may emit `while False`.


def fetch(src, key):
    try:
        if key in src:
            return src[key]
        return None
    except:
        return {}
