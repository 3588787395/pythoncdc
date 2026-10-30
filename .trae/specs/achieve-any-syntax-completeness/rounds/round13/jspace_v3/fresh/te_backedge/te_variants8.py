def v1(items):                        # s3 base: else last in for body
    out = []
    for a in items:
        try:
            v = int(a)
        except ValueError:
            pass
        else:
            out.append(v * 2)
    return out

def v2(items):                        # else last in while body
    out = []
    it = iter(items)
    while True:
        try:
            a = next(it)
        except StopIteration:
            break
        else:
            out.append(a)
    return out

def v3(items):                        # multi-statement else with inner if, last in loop
    out = []
    for a in items:
        try:
            v = int(a)
        except ValueError:
            pass
        else:
            if v > 0:
                out.append(v)
    return out

def v4(items):                        # else in loop, nested in function-level try
    out = []
    for a in items:
        try:
            v = int(a)
        except ValueError:
            out.append('err')
        else:
            out.append(v + 1)
    return out

def v5(items):                        # handler reraise, else last in loop
    out = []
    for a in items:
        try:
            v = int(a)
        except ValueError:
            raise
        else:
            out.append(v)
    return out

def v6(items):                        # else NOT last in loop (control: s4 shape)
    out = []
    for a in items:
        try:
            v = int(a)
        except ValueError:
            pass
        else:
            out.append(v)
        out.append(0)
    return out

def v7(items):                        # continue inside try body, else absent (W28 control)
    out = []
    for a in items:
        try:
            v = int(a)
            if v == 0:
                continue
        except ValueError:
            pass
        out.append(v)
    return out

def v8(items):                        # else contains continue via inner if (back-edge inside else)
    out = []
    for a in items:
        try:
            v = int(a)
        except ValueError:
            pass
        else:
            if v == 0:
                continue
            out.append(v)
    return out
