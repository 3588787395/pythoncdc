
def f(algo, datalist):
    tmporders = algo.tmporders.get_instance()
    try:
        for order_item in datalist:
            pass
        algo.tmporders.set_instance(tmporders)
    finally:
        algo.tmporders.write_lock.release()
