# synth a03r -- top-level `if A and B:` with for/continue sink, tail
# assignment after the if (klinedata witness shape, trimmed).
def synth_a03r_tail_after_boolop_if(symbols, count, query_date, frequency, include, fields=None, fq=None):
    his_data_dict = {}
    if include and query_date > 100:
        count_min = 0
        if count == 0:
            his_data_dict = get_kline_by_count_new(symbols, count, query_date, frequency, fields, fq, include)
            if len(his_data_dict) == 0:
                return his_data_dict
        else:
            for symbol in symbols:
                his = get_kline_by_count(symbol, count, query_date, '1m')
                if len(his) == 0:
                    continue
                his_data_dict[symbol] = his
                continue
        return his_data_dict
    his_data_dict = get_kline_by_count_new(symbols, count, query_date, frequency, fields, fq, include)
    return his_data_dict


def get_kline_by_count_new(symbols, count, query_date, frequency, fields, fq, include):
    return {'n': (symbols, count, query_date, frequency, fields, fq, include)}


def get_kline_by_count(symbol, count, query_date, frequency):
    return {'m': (symbol, count, query_date, frequency)}
