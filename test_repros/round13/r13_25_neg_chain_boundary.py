# -*- coding: utf-8 -*-
"""R13-C 负对照 3：三个「形状接近但必须保持 MATCH」的边界。

  * loop_arm_not_last       —— 链无 else 臂，落空臂不是**最后一个**臂（r13_04 的镜像）
  * raise_terminator_arms   —— 兄弟臂以 raise 终结而非 return
  * nothing_after_chain     —— 链后没有语句（merge 即函数出口）
  * chain_inside_for_plain_arms —— 链在 for 体内、臂尾都是普通语句（真实
    creat_sheet1 / set_parameters 的**内层**形状；本轮基线里它们的 -1/+2 已被
    R13-A3 的循环内 merge 修复翻正，此形状是那道修复的回归哨兵）

实测（run_all.py，严格尺子）：四个函数均 MATCH。
"""


def loop_arm_not_last(c, r, x):
    if c:
        for d in r:
            x = x + d
    elif r:
        return 1
    x = 7


def raise_terminator_arms(c, r, x):
    if c:
        raise ValueError('a')
    elif r:
        for d in r:
            x = x + d
    x = 7


def nothing_after_chain(c, r, x):
    if c:
        return 1
    elif r:
        for d in r:
            x = x + d
    else:
        return 2


def chain_inside_for_plain_arms(items, log, cfg):
    for k, v in items.items():
        if k == 'a':
            log.debug('a')
        elif k == 'b':
            log.debug('b')
        cfg[k] = v
    return cfg
