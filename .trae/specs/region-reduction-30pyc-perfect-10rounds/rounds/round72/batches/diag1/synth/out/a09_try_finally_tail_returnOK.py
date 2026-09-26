# Source Generated with Decompyle++ (Python version)
# File: a09_try_finally_tail_return.pyc (Python 3.11)

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
