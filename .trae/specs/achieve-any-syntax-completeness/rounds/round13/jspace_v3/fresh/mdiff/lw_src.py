def gen(diffs):
    for fromdata, todata, flag in diffs:
        fromlist, tolist = [], []
        while fromlist or tolist:
            if fromlist:
                fromdata = fromlist.pop(0)
            else:
                fromdata = ('', ' ')
            if tolist:
                todata = tolist.pop(0)
            else:
                todata = ('', ' ')
            yield (fromdata, todata, flag)
