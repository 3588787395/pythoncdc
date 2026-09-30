# -*- coding: utf-8 -*-
# R76-D1 复现（对照 Quote.run_tick_socket）：外层 try 内 `if message:`
# true 臂末尾是终结核 try/except；else 臂 return；if/else 之后的兄弟语句
# （stocks=...）预期被错误吸收进 true 臂。
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
        else:
            log('tick data empty')
            dataDict['updateflag'] = -1
            return None
        stocks = list(message.keys())[0]
        real_data = message.get(stocks)
        if real_data:
            if flag:
                panelt = {stocks: real_data}
    except TimeoutAgain:
        log('timeout')
    return panelt
