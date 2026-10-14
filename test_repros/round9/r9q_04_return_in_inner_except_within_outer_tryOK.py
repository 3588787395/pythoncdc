# Source Generated with Decompyle++ (Python version)
# File: r9q_04_return_in_inner_except_within_outer_try.pyc (Python 3.11)

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
                return None
            else:
                lg.warn('none')
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
