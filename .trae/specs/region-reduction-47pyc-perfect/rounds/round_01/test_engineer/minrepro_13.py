def while_loop_with_conditional_break(condition, max_iter):
    i = 0
    while True:
        if i >= max_iter:
            break
        if condition(i):
            continue
        i += 1
    return i
