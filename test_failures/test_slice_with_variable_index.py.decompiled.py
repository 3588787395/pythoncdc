def func(series, startDateIndex, endDateIndex):
    if len(series[startDateIndex:].index) > 0:
        tmpstartindex = series[startDateIndex:].index[0]
        if endDateIndex:
            tmpendindex = series[endDateIndex:].index[1]
        else:
            tmpendindex = None
            return (tmpstartindex, tmpendindex)
    else:
        tmpstartindex = None
