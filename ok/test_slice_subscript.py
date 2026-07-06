def func(stocks, source_start, source_end):
    panel = {}
    if isinstance(stocks, list):
        panel = panel[source_start:source_end]
    return panel
