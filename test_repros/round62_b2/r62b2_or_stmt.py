# -*- coding: utf-8 -*-
"""R62-b2 repro: statement shapes seen dropped in fly/data/quote_handler.pyc get_kline_local.

Original (landed-core) symptom: 5x  end_time = int(end[0:8] + (end[8:12] or '1530'))
absent from the decompiled product.
"""


def v1_call_arg_or(end):
    end_time = int(end[0:8] + (end[8:12] or '1530'))
    return end_time


def v2_plain_or(end):
    end_time = end or '1530'
    return end_time


def v3_sliced_no_or(end):
    end_time = int(end[0:8] + end[8:12])
    return end_time


def v4_or_no_call(end):
    end_time = end[0:8] or end[8:12]
    return end_time


def v5_elif_chain(end, k):
    if k == 1:
        end_time = int(end[0:8] + (end[8:12] or '1530'))
    elif k == 2:
        end_time = int(end[0:8] + (end[8:12] or '1530'))
    elif k == 3:
        end_time = int(end[0:8] + (end[8:12] or '1530'))
    else:
        end_time = 'none'
    return end_time


def v6_in_loop(end, xs):
    total = 0
    for x in xs:
        if x:
            end_time = int(end[0:8] + (end[8:12] or '1530'))
            total += end_time
    return total


def v7_and_variants(end):
    end_time = int(end[0:8] + (end[8:12] and '1530'))
    other = (end or 'a') and (end or 'b')
    return end_time + len(other)


def v8_try_body(end):
    try:
        end_time = int(end[0:8] + (end[8:12] or '1530'))
    except ValueError:
        end_time = 0
    return end_time
