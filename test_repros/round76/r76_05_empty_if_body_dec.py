# Source Generated with Decompyle++ (Python version)
# File: r76_05_empty_if_body.pyc (Python 3.11)

def f(data, preindex, series, start, end):
    for n in list(series):
        if data[preindex:n].empty:
            continue
        elif len(data[preindex:n].index) == 1:
            if list(data[preindex:n].index)[0] == start:
                continue
            if list(data[preindex:n].index)[0] == end:
                if preindex is None:
                    tmpdata = data[preindex:n]
                    if tmpdata[n:].empty:
                        tmpdata = tmpdata
                    else:
                        tmpdata = tmpdata[:-1]
                else:
                    tmp2 = data[preindex:n]
                    tmpdata = tmpdata.append(tmp2)
            if preindex != n:
                preindex = n
    return data
