def nested_except_if(a, b, info):
    try:
        result = eval(a)
        return result
    except:
        if a in info and b not in info:
            return None
        elif a in info:
            val = info[a]
            return val
    if a in info:
        val = repr(info[a])
        return val
    return a
