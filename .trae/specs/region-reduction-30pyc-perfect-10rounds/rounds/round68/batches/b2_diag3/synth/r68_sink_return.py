# -*- coding: utf-8 -*-
"""Minimal repro of klinedata::get_multiminute_his_data tail-return defect.

SOURCE SHAPE (byte-exact model of orig off 822/o161, off 2708/o518, off 2758/o533):
    if COND:                 # arm A: last stmt is an if/else whose merge is the arm end
        ...                  #  -> compiles to  JUMP_FORWARD to SINK
    else:                    # arm B: last stmt assigns the returned name
        x = g()              #  -> FALLS THROUGH into SINK
    return x                 # SINK: LOAD_FAST x ; RETURN_VALUE   (exactly one copy)
LANDED (wrong): emits `return x` inside arm A and leaves SINK as an implicit `return None`.
"""


def sink_return(cond, g, x):
    if cond:
        if len(x) == 0:
            y = 1
        else:
            y = 2
    else:
        x = g()
    return x
