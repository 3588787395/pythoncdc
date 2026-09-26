# F-CROSS (trade_info_utils query_strategy_id): try + with + if/else both
# returning + except + trailing return; the decompiler crosses the if-merge and
# try-tail JUMP_FORWARD targets.
def query_strategy_id(user_id, trade_id):
    sim_trading_list_path = user_id + '/' + trade_id
    if os.path.exists(sim_trading_list_path):
        try:
            with lock(sim_trading_list_path, mode='shared'):
                file_io = open(sim_trading_list_path)
                df = file_io.read()
            trade_df = df[df['id'] == trade_id]
            if len(trade_df) == 1:
                return trade_df.backtestContentId.iloc[0]
            else:
                return None
        except BaseException:
            log.error('err {}'.format(get_traceback_message()))
            time.sleep(1)
        return None


import os
import time

log = type('L', (), {'error': staticmethod(lambda *a: None)})()


def lock(path, mode='shared'):
    return open(path, 'w')


def get_traceback_message():
    return 'tb'
