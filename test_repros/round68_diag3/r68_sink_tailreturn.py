# -*- coding: utf-8 -*-
"""R68-diag3 synthetics: `if/else` whose two arms share ONE tail statement (`return x`).
Bytecode fingerprint of klinedata::get_multiminute_his_data tail:
    then-arm last block -> JUMP_FORWARD -> tail ; else block -> fall through -> tail
    tail = LOAD_FAST x ; RETURN_VALUE   (the only return of that value in the function)
Landed suspect: the tail `return x` gets pulled INTO the then-arm (because the analyzer puts
the tail block into IfRegion.then_blocks although it is the successor of merge/exit), and the
function then ends with an implicit `LOAD_CONST None ; RETURN_VALUE`."""


def sink_tailreturn_a(cond, x, f):
    his_data_dict = {}
    if cond and x:
        for symbol in x:
            his_data_dict[symbol] = 1
    else:
        his_data_dict = f()
    return his_data_dict


def sink_tailreturn_b(cond, x, f):
    his_data_dict = {}
    if cond:
        for symbol in x:
            his_data_dict[symbol] = 1
    else:
        his_data_dict = f()
    return his_data_dict


def sink_tailreturn_c(cond, x, f):
    his_data_dict = {}
    if cond and x:
        with open('a') as fh:
            for symbol in x:
                his_data_dict[symbol] = 1
    else:
        his_data_dict = f()
    return his_data_dict
