# R101-Pattern-E: for-else where loop body ends with continue (get_exrights_data)


def split(series, cut):
    res = {}
    for sec in series:
        if sec in cut:
            res[sec] = series[:sec]
            continue
        res[sec] = series[sec:]
    else:
        return res
    return res


def run(series, cut):
    return split(series, cut)
