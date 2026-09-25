# -*- coding: utf-8 -*-
"""Minimal repro of klinedata::get_all_real_daily_kline lost trailing `continue`.

SOURCE SHAPE (byte-exact model of orig 894/L1597 + 898 loop bottom):
    for s in syms:
        try:
            if c:            # arm A ends with an if/else -> jumps to the LOOP BOTTOM (2nd back edge)
                ...
            else:            # arm B ends with an explicit `continue` -> its own back edge,
                ...          #     carrying a line number, THEN the loop bottom's implicit one
                continue
        except BaseException:
            pass
    return x
LANDED (wrong): drops the explicit `continue` -> 1 fewer JUMP_BACKWARD pair (orig 216 vs 214).
"""


def sink_continue(syms, c, fields, kline, data_dict):
    for symbol in syms:
        try:
            if c:
                if fields is not None:
                    data_dict[symbol] = kline[fields]
                else:
                    data_dict[symbol] = kline
            else:
                if fields is not None:
                    data_dict[symbol] = kline[fields]
                else:
                    data_dict[symbol] = kline
                continue
        except BaseException:
            e = 1
    return data_dict
