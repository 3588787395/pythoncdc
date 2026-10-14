def r6_q6_widened_spec(x, y):
    if x:
        if y:
            one()
        else:
            two()
            return None
    elif y:
        three()
    merge()
