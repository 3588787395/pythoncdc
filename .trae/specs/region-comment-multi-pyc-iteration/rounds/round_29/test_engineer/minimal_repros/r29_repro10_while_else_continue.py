
def func_while_else_continue():
    i = 0
    while i < 10:
        i += 1
        if i % 2 == 0:
            continue
        if i == 7:
            break
    else:
        return "completed"
    return "broken"
