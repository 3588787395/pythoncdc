# F-FINALLYTAIL (ptradeAccount order/trade_response_order_update): try/finally at
# function tail where the finally normal-exit jumps to a trailing return block.
# The decompiler drops the explicit trailing `return None`, inlining the implicit
# return into the finally exit block.
def upd(algo, datalist):
    try:
        algo.lock.acquire()
        tmp = algo.get_instance()
        for item in datalist:
            if item in tmp:
                try:
                    obj = tmp[item]
                except BaseException:
                    obj = algo.create(item)
                obj.status = int(item['s'])
                tmp[item] = obj
        algo.set_instance(tmp)
    finally:
        algo.lock.release()
    return None
