def r9lo_02_andor_mix(engine, frequency, field, intervals):
    engine = Engine.instance()
    dt = engine.calendar_dt
    if engine.config.strategy.frequency == '1m' and frequency == '1d' or engine.phase() == ExecutionPhase.BEFORE_TRADING_START:
        dt = engine.data_proxy.get_previous_trading_date(engine.calendar_dt.date())
    return engine.data_proxy.get_history(self.asset, intervals, convert_dt_to_int(dt), frequency, field)
