def func(stocks, typet, start, end):
    data = {}
    retpanel = {}
    if isinstance(stocks, list):
        if typet == 6:
            if isinstance(stocks, str):
                stocks = [stocks]
            else:
                source_start = start[8:] or '0000'
                source_end = end[8:] or '1530'
                diffset = set(stocks)
                if len(diffset) == 0:
                    retpanel = data[source_start:source_end]
                    return retpanel
    return data
