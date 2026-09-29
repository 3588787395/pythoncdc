# -*- coding: utf-8 -*-
# [R75 fix1 synth] 负例：同族布尔条件（and / or 链），但不落在
# 「块尾条件跳转 fall-through = 区域 entry」的丢弃路径上，
# 两臂产物 sha 必须与落地逐字节相同，且 mandated 判据两侧均 success。
def neg_a(s, flag):
    if flag:
        return 0
    if '(' in s and ')' not in s:
        return 1
    if '[' in s or ']' not in s:
        return 2
    return 3

def neg_c(s):
    hit = 0
    if '(' in s:
        hit += 1
    elif 'x' in s and 'y' in s:
        hit += 2
    if '(' in s and ')' not in s or '[' in s and ']' not in s:
        hit += 4
    return hit
