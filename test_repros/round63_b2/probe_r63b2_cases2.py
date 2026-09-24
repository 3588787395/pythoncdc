# -*- coding: utf-8 -*-
"""R63 b2 probe 2: narrow the `return <chain> or <chain>` drop."""


def d1_elif_try(f, A, B, C, D):
    k = f.pop('k', '')
    if not isinstance(k, str):
        return False
    elif not k:
        try:
            cur = int(src())
        except BaseException:
            cur = 0
        return A < cur < B or C < cur < D


def d2_elif_notry(f, A, B, C, D):
    k = f.pop('k', '')
    if not isinstance(k, str):
        return False
    elif not k:
        cur = int(src())
        return A < cur < B or C < cur < D


def d3_if_try(f, A, B, C, D):
    k = f.pop('k', '')
    if not isinstance(k, str):
        return False
    if not k:
        try:
            cur = int(src())
        except BaseException:
            cur = 0
        return A < cur < B or C < cur < D


def d4_try_only(f, A, B, C, D):
    k = f.pop('k', '')
    try:
        cur = int(src())
    except BaseException:
        cur = 0
    return A < cur < B or C < cur < D


def d5_elif_try_plain_or(f, A, B, C, D):
    k = f.pop('k', '')
    if not isinstance(k, str):
        return False
    elif not k:
        try:
            cur = int(src())
        except BaseException:
            cur = 0
        return A or B


def d6_elif_try_two_chain_and(f, A, B, C, D):
    k = f.pop('k', '')
    if not isinstance(k, str):
        return False
    elif not k:
        try:
            cur = int(src())
        except BaseException:
            cur = 0
        return A < cur < B and C < cur < D


def d7_elif_try_assign(f, A, B, C, D):
    k = f.pop('k', '')
    if not isinstance(k, str):
        return False
    elif not k:
        try:
            cur = int(src())
        except BaseException:
            cur = 0
        r = A < cur < B or C < cur < D
        return r


def d8_elif_try_chain_or_plain(f, A, B, C, D):
    k = f.pop('k', '')
    if not isinstance(k, str):
        return False
    elif not k:
        try:
            cur = int(src())
        except BaseException:
            cur = 0
        return A < cur < B or C < D
