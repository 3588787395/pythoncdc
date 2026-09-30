# -*- coding: utf-8 -*-
# R76-G 复现（对照 Quote.run_individual_transform 简化）：
# while isSet: 外层 try { 内层 try { recv + if/else + eval try/except + 兄弟
# 语句 } except Again }。预期缺陷：内层 try 体语句丢失/位移。
def f(socket, deques, flag):
    panelt = None
    while is_set():
        try:
            try:
                message = socket.recv()
                if message:
                    try:
                        message = eval(message.decode())
                    except BaseException as x:
                        log('eval error')
                        log('content: ' + str(message))
                        continue
                else:
                    log('data empty')
                    continue
                stocks = list(message.keys())[0]
                real_data = message.get(stocks)
                if real_data:
                    panelt = {stocks: real_data}
                    deques.appendleft(panelt)
            except TimeoutAgain:
                log('timeout')
        except BaseException as ex:
            log('process error: ' + str(ex))
        sleep(0)
    return panelt
