# -*- coding: utf-8 -*-
"""Round 70 synth witness for the [25b] else-arm collapse guard.

Shape copied from IQCommon/util/trade_info_utils.pyc::trade_operation:
  * enclosing try/except inside a function that ends with an implicit `return`;
  * `if <cond>:` whose then-arm consists of exactly ONE `with` statement, with the
    whole body indented into the `with`;
  * the `if/else` is the LAST statement of the try block - nothing follows it;
  * an `else:` arm holding the trailing statements.

CPython then lays the with's "after" point out as
    cleanup -> is-None check -> LOAD_CONST None ; RETURN_VALUE -> <else body>
so the bare `return None` sits between then-arm and else arm. A decompiler that
collapses `else_succ` into "the statement after the if" (merge := else_succ) drops
the `else:` and loses those two instructions.

`trade_operation_witness_noelse` is the control: identical then-arm, no `else`, the
trailing call sits after the `if`. There the with's "after" point IS the trailing
call, no bare `return None` is produced, and the guard must stay silent.
"""
import os

TRADE_LIST_FILE = os.path.join(os.path.dirname(__file__), 'sim_trading_list.csv')
APP_LOG = []


def log_warning(msg):
    APP_LOG.append(msg)


def log_error(msg):
    APP_LOG.append(msg)


def trade_operation_witness(user_id, operation, csv_reader):
    trades = []
    try:
        if os.path.exists(TRADE_LIST_FILE):
            with open(TRADE_LIST_FILE, 'r') as handle:
                loaded = handle.read()
                for items in csv_reader:
                    if items in loaded:
                        if operation == 'start':
                            trades.append(items)
                            continue
                        trades.append((user_id, items))
                if not trades:
                    log_warning('empty %s' % user_id)
                    return False
        else:
            log_warning('missing %s' % user_id)
            return False
    except BaseException:
        log_error('boom')
        return False


def trade_operation_witness_noelse(user_id, operation, csv_reader):
    trades = []
    try:
        if os.path.exists(TRADE_LIST_FILE):
            with open(TRADE_LIST_FILE, 'r') as handle:
                loaded = handle.read()
                for items in csv_reader:
                    if items in loaded:
                        trades.append((user_id, items))
                if not trades:
                    return False
        log_warning('missing %s' % user_id)
        return False
    except BaseException:
        log_error('boom')
        return False
