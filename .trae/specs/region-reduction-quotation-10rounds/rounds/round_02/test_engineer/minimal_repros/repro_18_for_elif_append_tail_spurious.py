"""repro_18: for + if/elif 链 + append + 尾部 return 构造重发（one_prod_to_dataframe 变体）。

原始 one_prod_to_dataframe 在嵌套 for 循环后：
    columns = []
    if data_type is None:
        for item in fields: columns.append(...)
    else:
        columns = ['open', 'close', 'high', 'low', 'volume', 'money']
    return pandas.DataFrame(df, columns=columns, index=index)
反编译器在尾部多发出 11 条 spurious 指令（重复 return pandas.DataFrame(...)）。
本 repro 聚焦 Sequence 尾部 spurious 重发 + for/if-else/return 归约缺陷。
"""
import pandas


def one_prod_to_dataframe(data, prod_code, data_type=None):
    df = {}
    fields = data.get('fields')
    index = []
    time_index = None
    try:
        time_index = fields.index('business_time')
    except BaseException:
        system_log.error(get_traceback_message())
    try:
        time_index = fields.index('min_time')
    except BaseException:
        system_log.error(get_traceback_message())
    i = 0
    for item in fields:
        if time_index != i:
            df[get_real_param(item)] = []
        i = i + 1
    prod = data.get(prod_code)
    for item in prod:
        i = 0
        for v in item:
            if time_index != i:
                df[get_real_param(fields[i])].append(v)
            elif time_index is not None:
                v = str(v)
                if i == 0:
                    if len(v) == 8:
                        index.append(v[0:4] + '-' + v[4:6] + '-' + v[6:8])
                    elif len(v) == 10:
                        index.append(v[0:4] + '-' + v[4:6] + '-' + v[6:8] + ' ' + v[8:10])
            i = i + 1
    columns = []
    if data_type is None:
        i = 0
        for item in fields:
            if time_index != i:
                columns.append(get_real_param(item))
            i = i + 1
    else:
        columns = ['open', 'close', 'high', 'low', 'volume', 'money']
    return pandas.DataFrame(df, columns=columns, index=index)
