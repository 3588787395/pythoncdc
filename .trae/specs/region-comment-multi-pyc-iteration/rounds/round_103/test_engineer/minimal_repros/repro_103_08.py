def for_else_with_continue(symbols, data_dict):
    result = {}
    for symbol in symbols:
        if symbol in data_dict:
            result[symbol] = data_dict[symbol]
            continue
        result[symbol] = None
    else:
        return result
