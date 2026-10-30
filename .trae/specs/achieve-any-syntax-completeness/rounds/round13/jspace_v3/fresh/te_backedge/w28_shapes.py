def w1(xs):                       # W28 candidate: continue as last stmt of try body
    for x in xs:
        try:
            y = int(x)
            if y == 0:
                continue
        except ValueError:
            pass
        print(y)

def w2(xs):                       # bare continue at end of try body
    for x in xs:
        try:
            y = int(x)
            continue
        except ValueError:
            pass
        print(y)

def w3(xs):                       # handler continues, try body continues (pathological)
    for x in xs:
        try:
            y = int(x)
            continue
        except ValueError:
            continue
        print(y)

def w4(xs):                       # else: continue as last stmt (edge residual)
    for x in xs:
        try:
            y = int(x)
        except ValueError:
            pass
        else:
            continue
