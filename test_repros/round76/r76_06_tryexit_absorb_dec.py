# Source Generated with Decompyle++ (Python version)
# File: r76_06_tryexit_absorb.pyc (Python 3.11)

def f(socket, dataDict, flag):
    imagedata = dataDict['imagedata']
    panelt = None
    try:
        message = socket.recv()
        if message:
            try:
                message = eval(message.decode())
            except BaseException as x:
                log('eval tick error')
                log('content: ' + str(message))
                log('exc: ' + str(x))
                return None
            stocks = list(message.keys())[0]
            real_data = message.get(stocks)
            if real_data and flag:
                panelt = {stocks: real_data}
        else:
            log('tick data empty')
            dataDict['updateflag'] = -1
            return None
    except TimeoutAgain:
        log('timeout')
    return panelt
