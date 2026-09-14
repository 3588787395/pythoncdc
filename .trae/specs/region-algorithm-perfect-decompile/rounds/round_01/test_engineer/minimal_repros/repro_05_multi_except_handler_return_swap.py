def multi_except(data, info, trans):
    try:
        params = eval(data)
        return data
    except:
        if data in info:
            if info[data] not in trans:
                return None
            value = trans[data]
            return value
        if data in trans:
            value = trans[data]
            return value
        return data
