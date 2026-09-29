# -*- coding: utf-8 -*-
# [R75 fix2 synth] 负例：与 repro 同族但两臂必须逐字节相同。
#   neg_try_for  break 目标在 try 体内（属 region.blocks）
#   neg_pure_tail 分支尾块含用户语句后再隐式 return None
#                （edit-D2 纯度判据必须拒绝剔除，否则语句外提）
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
        log.append("done")
    return 0
