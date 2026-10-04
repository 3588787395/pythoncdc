# Source Generated with Decompyle++ (Python version)
# File: v_b75_face.pyc (Python 3.11)

global _CACHE
__doc__ = 'rv2 变体面 B75（r10_15 g_in_try_except 邻域）：两臂 return 互换 / finally 无条件段'
_CACHE = {}
def v_swap_arm_returns(key):
    if _CACHE:
        print('hit')
        return 'miss'
    else:
        return 'miss'
    try:
        pass
    except KeyError:
        _CACHE[key]
        if _CACHE:
            return print('hit')
        else:
            return None
    finally:
        if _CACHE:
            print('hit')
def n_fin_noseg(key):
    try:
        return _CACHE[key]
    except KeyError:
        print('done')
        return 'miss'
    finally:
        print('done')
