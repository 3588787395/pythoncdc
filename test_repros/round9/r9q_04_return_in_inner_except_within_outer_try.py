def tick(sock, dq, lk, lg):
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
                panelt = {stocks: real_data}
            else:
                lg.warn('none')
        else:
            lg.warn('empty')
            return None
    except Again:
        lg.error('timeout')
    except BaseException as ex:
        lg.error(str(ex))
