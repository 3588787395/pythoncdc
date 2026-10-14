# Source Generated with Decompyle++ (Python version)
# File: r9q_13_tick_nested_except_return_and_elif.pyc (Python 3.11)

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
                        return None
                    else:
                        return None
                elif message[stocks][-1] == 1 and panelt is not None:
                    if flag:
                        dq.appendleft(panelt)
                        return None
                else:
                    return None
                return None
        else:
            lg.warn('empty')
            return None
    except Again:
        lg.error('timeout')
        return None
    except BaseException as ex:
        lg.error(str(ex))
        return None
