def f_else(algo, datalist):
    try:
        x = algo.get()
        for item in datalist:
            pass
        else:
            algo.set(x)
    finally:
        algo.release()

def f_after(algo, datalist):
    try:
        x = algo.get()
        for item in datalist:
            pass
        algo.set(x)
    finally:
        algo.release()
