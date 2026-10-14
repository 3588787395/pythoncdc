def r6_q3_forhost_spec(xs):
    for x in xs:
        if x:
            one()
        elif x > 1:
            two()
            return None
        step(x)
