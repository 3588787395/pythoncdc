"""repro_12: for 循环后尾部 spurious 重发 return 语句（one_prod_to_dataframe +11 模式）。

原始 one_prod_to_dataframe 尾部正确 return 后，反编译器多发出 11 条指令：
BUILD_LIST / LIST_EXTEND / STORE_FAST 'columns' / LOAD_GLOBAL 'pandas' /
LOAD_ATTR 'DataFrame' / ... / RETURN_VALUE，即重复发射 `return pandas.DataFrame(df, columns=columns, index=index)`。
本 repro 聚焦 Sequence 尾部 spurious 重发缺陷。
"""
import pandas


def one_prod_to_dataframe(data, prod_code, data_type=None):
    time_index = []
    prod = data.get(prod_code)
    columns = ['open', 'close', 'high', 'low', 'volume', 'money']
    df = pandas.DataFrame(columns=columns)
    for item in prod:
        i = 0
        for v in item:
            if time_index[i] != v:
                pass
            i += 1
        df = df.append(item)
    return pandas.DataFrame(df, columns=columns, index=index)
