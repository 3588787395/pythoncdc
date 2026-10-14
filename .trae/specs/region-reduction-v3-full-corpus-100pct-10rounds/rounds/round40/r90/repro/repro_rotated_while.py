import time


def sync_worker(pre_before_trading, post_after_trading, holiday_sync_account, engine, active):
    while True:
        while (int(datetime.datetime.now().strftime('%H%M')) < pre_before_trading
                or int(datetime.datetime.now().strftime('%H%M')) >= post_after_trading
                or (holiday_sync_account == '0'
                    and not engine.data_proxy.is_trading_date(datetime.datetime.now().date()))):
            time.sleep(60)
        while (pre_before_trading <= int(datetime.datetime.now().strftime('%H%M'))
                < int(post_after_trading)):
            time.sleep(1)
        time.sleep(2)
