# Source Generated with Decompyle++ (Python version)
# File: r9a1_04_pastconfluence_chain.pyc (Python 3.11)

def r9a1_04_pastconfluence_chain(engine, frequency, phase, dt, proxy):
    if engine.config.strategy.frequency == '1m' and frequency == '1d' or phase() == 'BEFORE':
        dt = proxy.get_previous_trading_date(engine.calendar_dt.date())
    return proxy.get_history(engine.asset, dt, frequency)
