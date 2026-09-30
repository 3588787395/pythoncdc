# -*- coding: utf-8 -*-
def neg_a(s, flag):
    if flag:
        return 0
    if '(' in s and ')' not in s:
        return 1
    if '[' in s or ']' not in s:
        return 2
    return 3

def neg_b(a, b, c):
    total = 0
    if a and b:
        total += 1
    if b or c:
        total += 2
    if a and b or c:
        total += 4
    return total
