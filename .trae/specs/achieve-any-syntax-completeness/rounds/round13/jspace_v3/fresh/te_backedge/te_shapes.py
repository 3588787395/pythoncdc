def s1(xs):                       # W28 candidate: continue inside try body, code after try
    for x in xs:
        try:
            if x == 0:
                continue
            y = int(x)
        except ValueError:
            pass
        print(y)

def s3(wrapped, assigned):        # our shape: else last stmt in loop body
    out = []
    for attr in assigned:
        try:
            value = getattr(wrapped, attr)
        except AttributeError:
            pass
        else:
            setattr(wrapped, attr, value)
            out.append(attr)
    return out

def s4(wrapped, assigned):        # else NOT last: stmt after else
    out = []
    for attr in assigned:
        try:
            value = getattr(wrapped, attr)
        except AttributeError:
            pass
        else:
            out.append(attr)
        out.append(1)
    return out

def s5(wrapped, assigned):        # no else: stmt after try
    out = []
    for attr in assigned:
        try:
            value = getattr(wrapped, attr)
        except AttributeError:
            pass
        out.append(attr)
    return out
