
def func_empty_except():
    try:
        x = 1
    except:
        pass
    try:
        y = 2
    except:
        pass
    return x + y
