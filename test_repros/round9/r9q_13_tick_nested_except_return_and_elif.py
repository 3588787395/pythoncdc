def tick(sock, dq, lk, lg, flag):
    panelt = None
    try:
        message = sock.recv()
        if message:
            try:
                message = eval(message)
            except BaseException as x:
                lg.error(str(x))
                return None
            stocks = list(message.keys())[0]
            real_data = message.get(stocks)
            if real_data:
                if real_data[-1] == 0:
                    tick_returnDf = get_tick(stocks, real_data)
                    if flag:
                        dq.appendleft(tick_returnDf)
                elif message[stocks][-1] == 1 and panelt is not None and flag:
                    dq.appendleft(panelt)
        else:
            lg.warn('empty')
            return None
    except Again:
        lg.error('timeout')
    except BaseException as ex:
        lg.error(str(ex))
