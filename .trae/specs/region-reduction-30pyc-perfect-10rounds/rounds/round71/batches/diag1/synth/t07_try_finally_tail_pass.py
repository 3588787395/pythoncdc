# F-FINALLYTAIL variant: trailing no-op statement after try/finally (orig pyc has
# the tail-return block after the exception machinery; a trailing statement is
# what forces that layout in CPython).
def upd2(algo, datalist):
    try:
        algo.lock.acquire()
        for item in datalist:
            algo.put(item)
    finally:
        algo.lock.release()
    pass
