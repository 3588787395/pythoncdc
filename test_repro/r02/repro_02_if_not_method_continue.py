while True:
    if not is_trading_date(today()):
        continue
    now = datetime.now()
