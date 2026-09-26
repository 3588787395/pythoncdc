# F-ORELSE (trade_info_utils kill_trade_process, klinedata get_kline_by_count_new,
# strategy __init__): None-guard chain where each guard's false path targets the
# merge; decompiler re-targets guards to a farther merge, skipping cleanup.
def kill(process_id, path):
    if process_id is not None:
        process_id = process_id.replace('\n', '')
        try:
            os.unlink(path)
        except OSError:
            pass
    if os.path.exists(path):
        os.unlink(path)
    return process_id


import os
