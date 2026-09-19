# Source Generated with Decompyle++ (Python version)
# File: r2_01_set_trade_status_collapse.pyc (Python 3.11)

__doc__ = """Repro: set_trade_status collapse (160 instrs -> `pass`, decomp=3).

Pattern: while-loop containing try/except BaseException, and the try
body contains `with ctx(): ... break` -- a `break` INSIDE the with
body. CPython: the break emits the __exit__ cleanup then
JUMP_FORWARD straight to the return block; the loop bottom-test is
reached only via the with-except/except-handler exits.

Failure chain (verified by debugging the region pipeline on the
original code object):
  1. the while LoopRegion gets has_break=True;
  2. _loop_generate_while takes the break-folding path and calls
     _fold_break_to_return_w (region_ast_generator.py ~6000);
  3. that helper does s.get('orelse', []) then len(_orelse), but the
     loop-body If emitters produce If nodes with 'orelse': None -> TypeError;
  4. pycdc.py catches the exception and emits the function as `pass`.

Original: trade_info_utils.pyc::set_trade_status -- first_diff idx1:
LOAD_CONST(1) vs LOAD_CONST(None).
"""
import os
FileLock = open
FileIO = open
system_log = print
def get_traceback_message():
    return 'tb'
def set_trade_status(trade_id, status, user_id=None):
    count = 1
    exchange_flag = False
    if user_id is not None:
        sim_trading_list_path = os.path.join('d', user_id, 'list.csv')
    else:
        sim_trading_list_path = os.path.join('d', 'list.csv')
    if os.path.exists(sim_trading_list_path):
        while count <= 3:
            try:
                with FileLock(sim_trading_list_path):
                    file_io = FileIO(sim_trading_list_path)
                    csv_reader = file_io.read(return_type='csv_reader')
                    write_info = []
                    for items in csv_reader:
                        if len(items) > 0:
                            if items[0] == trade_id:
                                items[2] = status
                                exchange_flag = True
                            write_info.append(items)
                    if len(write_info) > 0 and exchange_flag is True:
                        file_io.write(write_info, mode='w', data_type='list')
                break
            except BaseException:
                system_log.error(f'第{count}次失败，原因：{get_traceback_message()}')
                count += 1
    else:
        system_log.error('%s不存在' % sim_trading_list_path)
    return exchange_flag
