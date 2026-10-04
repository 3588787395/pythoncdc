"""rv2 变体面 B75（r10_15 g_in_try_except 邻域）：两臂 return 互换 / finally 无条件段"""

_CACHE = {}


def v_swap_arm_returns(key):
    global _CACHE
    try:
        return "miss"
    except KeyError:
        return _CACHE[key]
    finally:
        if _CACHE:
            print("hit")


def n_fin_noseg(key):
    global _CACHE
    try:
        return _CACHE[key]
    except KeyError:
        return "miss"
    finally:
        print("done")
