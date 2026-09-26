# F-THENOVER/adjacent-return (trade_info_utils query_trade_strategy_info /
# query_strategy_id / flytools set_userid_containerid_dict): `if ...: body / else:
# return None` followed by the implicit end `return None` yields two adjacent
# return-None blocks; decompiler re-attaches the arm so the guard's jump re-targets
# the second block (A@196 -> 614 vs B -> 618).
import os


def query(path, csv_reader, trade_status):
    if os.path.exists(path):
        try:
            for items in csv_reader:
                if len(items) > 0 and items[2] in trade_status:
                    return True
        except BaseException:
            print('error')
    else:
        return None
