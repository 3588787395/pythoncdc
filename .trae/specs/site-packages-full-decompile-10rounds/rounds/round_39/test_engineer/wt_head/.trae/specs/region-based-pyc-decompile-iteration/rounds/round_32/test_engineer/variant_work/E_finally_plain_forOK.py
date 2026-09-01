# Source Generated with Decompyle++ (Python version)
# File: E_finally_plain_for.pyc (Python 3.11)

def f(algo, datalist):
    tmporders = algo.tmporders.get_instance()
    try:
        for order_item in datalist:
            pass
        else:
            algo.tmporders.set_instance(tmporders)
    finally:
        algo.tmporders.write_lock.release()
