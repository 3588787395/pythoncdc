def elif_and_chain(msgs, panelt, flag, dq, lg):
    for m in msgs:
        stocks = m[0]
        real_data = m[1]
        if real_data:
            if real_data[-1] == 0:
                df = get_tick(stocks, real_data)
                if flag:
                    dq.appendleft(df)
            elif m[stocks][-1] == 1 and panelt is not None and flag:
                dq.appendleft(panelt)
        else:
            lg.warn('none')
