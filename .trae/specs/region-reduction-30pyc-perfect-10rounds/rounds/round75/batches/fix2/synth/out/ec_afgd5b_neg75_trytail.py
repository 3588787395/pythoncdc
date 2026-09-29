# Source Generated with Decompyle++ (Python version)
# File: neg75_trytail.pyc (Python 3.11)

import os
def neg_try_for(n):
    total = 0
    try:
        for i in range(n):
            if i % 7 == 0:
                break
            total += i
        return total
    except BaseException:
        return -1
def neg_pure_tail(new_assets, cond, log):
    if cond:
        return 1
    else:
        new_assets = list(new_assets)
        for item in new_assets:
            if item:
                break
        del new_assets
        log.append('done')
        return 0
