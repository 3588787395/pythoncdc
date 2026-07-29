"""repro_02: try/except BaseException + for 循环 + 尾部 DataFrame 构造（one_prod_to_dataframe 模式）。

复现原始字节码结构：两个连续 try/except BaseException 块，后接 for 循环，
函数尾有 pandas.DataFrame(df, columns=..., index=...) 构造。
反编译器在函数尾多出 11 条 spurious 指令（重复 DataFrame 构造）。
对应 _identify_try_except_regions + _identify_sequence_regions 尾部重发。
"""


def one_prod(data, prod_code):
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
            df[item] = get_real_param(item)
        i = i + 1
    columns = ['open', 'close', 'high', 'low', 'volume', 'money']
    return pandas.DataFrame(df, columns=columns, index=index)
