# -*- coding: utf-8 -*-
"""Round 48-C witness battery.

w*  = the buy_close/sell_close shape (else-body heads with a nested plain `if`
      that is followed by trailing statements, while the then-arm jumps past
      them).  Must be defective on landed bytes and clean on the arm.
c*  = negative controls: genuine elif chains / clean else bodies.  Must be
      non-defective and signature-identical on both sides.
s*  = sibling shapes of the same family that this predicate does NOT reach
      (documented for handover); signature-identical on both sides.
"""

_BOX = {}


def _set(name, val):
    _BOX[name] = val


def w1_close_shape(flag, other, n):
    if flag == 'stop':
        _set('r', 0)
        return None
    if other == 'A':
        if flag:
            _set('a', 1)
            if n == 0:
                _set('b', 2)
                return None
        else:
            _set('a', 3)
    else:
        if flag:
            _set('c', 4)
        _set('a', 5)
        _set('b', 6)
    if n == 0:
        _set('d', 7)
        return None
    elif n < 3:
        _set('d', 8)
        n = 9
    return n


def w2_close_shape_twin(flag, other, n):
    if flag == 'stop':
        _set('r', 0)
        return None
    if other == 'B':
        if flag:
            _set('a', 21)
            if n:
                return None
        else:
            _set('a', 22)
    else:
        if other:
            _set('c', 23)
        _set('a', 24)
        _set('b', 25)
    if n > 1:
        return None
    elif n < 3:
        _set('d', 26)
    return n


def c1_real_elif_no_else(flag, other, n):
    if flag == 'stop':
        return None
    elif other == 'A':
        if flag:
            _set('a', 31)
            if n == 0:
                return None
        else:
            _set('a', 32)
    elif flag:
        _set('c', 33)
    _set('a', 34)
    _set('b', 35)
    if n == 0:
        return None
    elif n < 3:
        _set('d', 36)
    return n


def c2_real_elif_else(flag, other, n):
    if flag == 'stop':
        return None
    elif other == 'A':
        _set('a', 41)
    elif n:
        _set('b', 42)
    else:
        _set('c', 43)
    _set('d', 44)
    return n


def c3_else_head_nested_if_with_own_else(flag, other, n):
    if flag == 'stop':
        return None
    if other == 'A':
        _set('a', 51)
    else:
        if n:
            _set('b', 52)
        else:
            _set('c', 53)
    return n


def c4_plain_if_else_two_arms(flag, other, n):
    if flag:
        _set('a', 61)
    else:
        if other:
            _set('b', 62)
        else:
            _set('c', 63)
        _set('d', 64)
    return n


def c5_elif_chain_all_terminal(flag, other, n):
    if flag == 'x':
        return 1
    elif flag == 'y':
        return 2
    elif other == 'z':
        return 3
    _set('a', 71)
    return n


def c6_real_elif_then_nested_head_tail(flag, other, n):
    if flag == 'stop':
        return None
    elif other == 'A':
        if flag:
            _set('a', 81)
        else:
            _set('a', 82)
    elif n:
        _set('b', 83)
    else:
        _set('c', 84)
    _set('d', 85)
    return n


def s1_else_head_if_then_tail(flag, other, n):
    if flag == 'stop':
        return None
    if other == 'A':
        _set('a', 91)
    else:
        if flag:
            _set('b', 92)
        _set('c', 93)
    return n


def s2_else_head_if_own_else_tail(flag, other, n):
    if flag == 'stop':
        return None
    if other == 'A':
        _set('a', 101)
    else:
        if n:
            _set('b', 102)
        else:
            _set('c', 103)
        _set('d', 104)
    return n


def s3_else_head_if_then_tail_two_tails(flag, other, n):
    if flag == 'stop':
        return None
    if other == 'A':
        if flag:
            _set('a', 111)
        else:
            _set('a', 112)
    else:
        if n:
            _set('c', 113)
        _set('e', 114)
        _set('f', 115)
    return n
