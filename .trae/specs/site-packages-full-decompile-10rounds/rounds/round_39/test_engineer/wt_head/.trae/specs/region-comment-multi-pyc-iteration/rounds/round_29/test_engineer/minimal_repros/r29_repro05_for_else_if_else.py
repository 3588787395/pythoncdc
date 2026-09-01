
def func_for_else_if_else():
    for x in range(10):
        if x == 5:
            break
    else:
        if x > 3:
            print("big")
        else:
            print("small")
        return x
