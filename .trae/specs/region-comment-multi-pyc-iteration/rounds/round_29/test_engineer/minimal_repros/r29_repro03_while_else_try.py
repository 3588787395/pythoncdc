
def func_while_else_try():
    while True:
        x = 1
        if x:
            break
    else:
        try:
            y = 2
        except:
            y = 0
        return y
