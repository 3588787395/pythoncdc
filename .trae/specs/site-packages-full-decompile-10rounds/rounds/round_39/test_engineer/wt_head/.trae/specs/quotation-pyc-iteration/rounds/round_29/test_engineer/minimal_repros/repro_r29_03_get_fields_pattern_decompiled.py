# Source Generated with Decompyle++ (Python version)
# File: repro_r29_03_get_fields_pattern.pyc (Python 3.11)

def f(fans, fields):
    d = {1: 2, 3: 4}
    if fans == 1:
        d = d[1]
        result = []
        for k in d:
            result.extend(d[k])
        return result
    elif fans == 2:
        d = d[2]
    elif fans == 3:
        d = d[3]
    elif fans in d.keys():
        d = d[fans]
        if not fields:
            return d
        else:
            return fields
    elif fields is None:
        pass
