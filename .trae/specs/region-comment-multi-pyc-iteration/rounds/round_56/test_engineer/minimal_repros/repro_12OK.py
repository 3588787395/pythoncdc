# Source Generated with Decompyle++ (Python version)
# File: repro_12.pyc (Python 3.11)

def repro_12(data_dict, field_list, kline_ndarray):
    for f in list(set(field_list) - {'price'}):
        for i in range(len(data_dict['datetime'])):
            try:
                kline_ndarray[f][i] = data_dict[f][i]
            except:
                continue
    else:
        kline_ndarray['price'] = kline_ndarray['close']
        return kline_ndarray
