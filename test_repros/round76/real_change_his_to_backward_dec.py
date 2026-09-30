# Source Generated with Decompyle++ (Python version)
# File: real_change_his_to_backward.pyc (Python 3.11)

def change_his_to_backward(self, security, data, exrights_data, start, end):
    if len(data) == 0:
        return data
    else:
        firstdate = list(data.index)[0].tz_localize(None).to_pydatetime().strftime('%Y%m%d')
        if start != firstdate:
            start = firstdate
        if len(start) > 8:
            start = start[:8]
        if len(end) > 8:
            end = end[:8]
        startDateIndex = qdt.datetime.strptime(start, '%Y%m%d').strftime('%Y-%m-%d 00:00:00')
        endDateIndex = qdt.datetime.strptime(end, '%Y%m%d').strftime('%Y-%m-%d 00:00:00')
        fields = ['open', 'close', 'high', 'low', 'price']
        series = exrights_data[security]
        if series.empty:
            return data
        elif series[:endDateIndex].empty:
            return data
        elif startDateIndex == endDateIndex:
            n = list(series[:endDateIndex].index)[-1]
            data = data * float(series.loc[n, 'exer_backward_a']) + float(series.loc[n, 'exer_backward_b'])
            return data
        else:
            preindex = None
            tmpdata = None
            if len(series[:startDateIndex].index) > 1:
                tmpstartindex = series[:startDateIndex].index[-1]
            else:
                tmpstartindex = None
        if len(series[endDateIndex:].index) > 0:
            tmpendindex = series[endDateIndex:].index[0]
        else:
            tmpendindex = None
        for n in list(series[tmpstartindex:tmpendindex].index):
            if preindex is None:
                tmpdata = data[:n][:-1]
            elif data[preindex:n].empty or list(data[preindex:n].index)[-1].tz_localize(None) != pandas.Timestamp(qdt.datetime.strptime(n, '%Y-%m-%d 00:00:00')):
                break
            else:
                data.loc[preindex:data[preindex:n][:-1].index[-1], fields] = data[preindex:n][:-1][fields] * float(series.loc[preindex, 'exer_backward_a']) + float(series.loc[preindex, 'exer_backward_b'])
                tmpdata = tmpdata.append(data[preindex:n][:-1])
            if preindex != n:
                preindex = n
        if preindex:
            data.loc[preindex:, fields] = data[preindex:][fields] * float(series.loc[preindex, 'exer_backward_a']) + float(series.loc[preindex, 'exer_backward_b'])
            tmpdata = tmpdata.append(data[preindex:])
        if tmpdata is not None:
            data = tmpdata
        return data
