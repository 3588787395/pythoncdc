def func(stocks, source_start, source_end):
    panel = {}
    if isinstance(stocks, list):
        data = panel[(stocks, slice(source_start, source_end))]
    return data
