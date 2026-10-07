def r9lo_06_ctl_nested_if(a, b, out):
    if a:
        if b:
            out.add(a)
    if b and a == 1:
        out.add(b)
    return out
