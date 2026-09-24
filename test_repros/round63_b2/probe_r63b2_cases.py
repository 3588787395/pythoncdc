# -*- coding: utf-8 -*-
"""R63 b2 probe: which ingredient drops the elif-branch tail return?"""


def c1_elif_try_plain(f, A, B, C, D):
    k = f.pop('k', '')
    if not isinstance(k, str):
        return False
    elif not k:
        try:
            cur = int(src())
        except BaseException:
            cur = 0
        return cur


def c2_elif_try_chain(f, A, B, C, D):
    k = f.pop('k', '')
    if not isinstance(k, str):
        return False
    elif not k:
        try:
            cur = int(src())
        except BaseException:
            cur = 0
        return A < cur < B


def c3_elif_try_or(f, A, B, C, D):
    k = f.pop('k', '')
    if not isinstance(k, str):
        return False
    elif not k:
        try:
            cur = int(src())
        except BaseException:
            cur = 0
        return A < cur or C < D


def c4_if_try_chain(f, A, B, C, D):
    k = f.pop('k', '')
    if not isinstance(k, str):
        return False
    if not k:
        try:
            cur = int(src())
        except BaseException:
            cur = 0
        return A < cur < B
    return 0


def c5_elif_nochain_try(f, A, B, C, D):
    k = f.pop('k', '')
    if not isinstance(k, str):
        return False
    elif not k:
        try:
            cur = int(src())
        except BaseException:
            cur = 0
        return A < cur < B or C < D < A


def c6_elif_try_then_more(f, A, B, C, D):
    k = f.pop('k', '')
    if not isinstance(k, str):
        return False
    elif not k:
        try:
            cur = int(src())
        except BaseException:
            cur = 0
        cur = cur + 1
        return A < cur < B


def c7_elif_try_pass(f, A, B, C, D):
    k = f.pop('k', '')
    if not isinstance(k, str):
        return False
    elif not k:
        try:
            cur = int(src())
        except BaseException:
            pass
        return A < cur < B


def c8_elif_chain_only(f, A, B, C, D):
    k = f.pop('k', '')
    if not isinstance(k, str):
        return False
    elif not k:
        return A < k < B
