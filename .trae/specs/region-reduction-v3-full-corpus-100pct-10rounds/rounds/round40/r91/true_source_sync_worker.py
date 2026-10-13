import time
datetime=None
def _sync_worker(self, engine):
    steps = self.engine.config.plugins.plugin_system_trade.account_sync_steps
    engine.set_engine(engine)
    if self.business_type == 'future':
        pre_before_trading = future_pre_before_trading
        post_after_trading = future_post_after_trading
    elif self.business_type == 'hks':
        pre_before_trading = hks_pre_before_trading
        post_after_trading = hks_post_after_trading
    else:
        pre_before_trading = stock_pre_before_trading
        post_after_trading = stock_post_after_trading
    while True:
        while int(datetime.datetime.now().strftime('%H%M')) < pre_before_trading or int(datetime.datetime.now().strftime('%H%M')) >= int(post_after_trading) or holiday_sync_account == '0' and not self.engine.data_proxy.is_trading_date(datetime.datetime.now().date()):
            time.sleep(60)
        if self.engine.data_proxy.is_trading_date(datetime.datetime.now().date()):
            if self.reconnect_flag is False:
                if datetime.datetime.now().date() == self.first_run_date and self.first_run_time < 900 or datetime.datetime.now().date() != self.first_run_date:
                    if int(datetime.datetime.now().strftime('%H%M')) >= 900:
                        system_log.debug('MSG')
                        if not reconnect(self.broker.trade_account, self.trade_id):
                            return
                        self.reconnect_flag = True
        while pre_before_trading <= int(datetime.datetime.now().strftime('%H%M')) < int(post_after_trading):
            sync_data_flag = 0
            with self.order_or_trade_lock:
                if self.receive_order_response_flag == 1 or self.receive_trade_response_flag == 1:
                    sync_data_flag = 1
                    self.receive_order_response_flag = 0
                    self.receive_trade_response_flag = 0
            time_difference = abs((datetime.datetime.now() - self.sync_account_time).total_seconds())
            if time_difference > sync_max_time:
                sync_data_flag = 1
            if sync_data_flag:
                self.sync_account()
                self.sync_account_time = datetime.datetime.now()
            if len(self.on_order_response_list) > 0:
                on_order_response_handle(self.on_order_response_list)
            if len(self.on_trade_response_list) > 0:
                on_trade_response_handle(self.on_trade_response_list)
            time.sleep(steps)
        time.sleep(steps)
