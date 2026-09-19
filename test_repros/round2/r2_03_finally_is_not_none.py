"""Repro: get_trade_unit_info finally-condition bug.

Faithful skeleton: outer for-loop; a first try/except wrapping a
`with FileLock(...)` read whose handler ends with `return None`; then
a try/except/finally as the loop body's LAST statement whose finally
is `if fp is not None: fp.close()`, so CPython points the
finally's POP_JUMP_FORWARD_IF_NONE at the loop back-edge (orig
1296-1342: PJ_NONE->1342; close(); JUMP_BACKWARD->94).

The decompiler renders it as `if not fp:` (truthiness negation) --
the None comparison is lost and the code would crash close() on None.
"""
import csv
import os

FileLock = open
FileIO = open
app_log = print

TRADE_DIR_PATH = 'd'
SIM_TRADING_LIST_FILE = 'list.csv'


def get_traceback_message():
    return 'tb'

def get_trade_unit_info():
    tempTradeUnits = []
    parent, dirs, files = next(os.walk(TRADE_DIR_PATH))
    for user in dirs:
        tempBacktestIds = []
        trade_list_file = os.path.join(TRADE_DIR_PATH, user, SIM_TRADING_LIST_FILE)
        try:
            if os.path.exists(trade_list_file):
                with FileLock(trade_list_file, mode='shared'):
                    csv_reader = FileIO(trade_list_file).read(return_type='csv_reader')
                for line in csv_reader:
                    if line[2] == '0' or line[2] == '3':
                        tempBacktestIds.append(line[0])
        except BaseException:
            app_log.info(f'读取{trade_list_file!s}文件失败，错误为{get_traceback_message()!s}')
            return None
        if len(tempBacktestIds) > 0:
            user_info_file = os.path.join(TRADE_DIR_PATH, user, 'u.csv')
            if os.path.exists(user_info_file):
                fp = None
                try:
                    fp = open(user_info_file, 'r', encoding='utf-8')
                    for item in csv.reader(fp):
                        if item[0] in tempBacktestIds:
                            if len(item) >= 5:
                                tempTradeUnits.append(str(item[4]))
                            if len(item) >= 7 and item[6]:
                                tempTradeUnits.append(str(item[6]))
                except BaseException:
                    app_log.info(f'读取{user_info_file!s}文件失败,错误为 {get_traceback_message()!s}')
                finally:
                    if fp is not None:
                        fp.close()
    return tempTradeUnits
