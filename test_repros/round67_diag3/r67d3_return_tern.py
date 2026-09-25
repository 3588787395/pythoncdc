# -*- coding: utf-8 -*-
"""r67-diag3 synthetic repro: `return <dict/tuple>, <ternary>` demoted to a bare
Expr statement (losing the RETURN_VALUE) and the all-constant-key dict
(BUILD_CONST_KEY_MAP) collapsed to a one-pair BUILD_MAP."""


def s1(error_dict, is_dict):
    return error_dict, ({} if is_dict else [])


def s2(is_dict):
    return {'error_no': -1, 'error_info': 'm'}, ({} if is_dict else [])


def s3(is_dict):
    return {'error_no': 1, 'error_info': 2}


def s4(a, b):
    d = {'error_no': a, 'error_info': b}
    return d


def s5(a, b, is_dict):
    return {'error_no': a, 'error_info': b}, ({} if is_dict else [])


def s6(a, is_dict):
    return a, ({} if is_dict else [])
