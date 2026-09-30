# Source Generated with Decompyle++ (Python version)
# File: r76_04_or_armswap_dec.pyc (Python 3.11)

def f(data, series, preindex):
    tmpdata = None
    for n in list(series):
        if preindex is None:
            tmpdata = data[:n][:-1]
        elif data[preindex:n].empty or list(data[preindex:n])[-1] == n:
            data2 = data[preindex:n][:-1]
            tmpdata = tmpdata.append(data2)
        else:
            break
        if preindex != n:
            preindex = n
    if preindex:
        tmpdata = tmpdata.append(data[preindex:])
    return tmpdata
