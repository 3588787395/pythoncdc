"""repro_05: 复现 one_prod_to_dataframe 反编译缺陷（函数尾生成多余代码 +11）。

缺陷模式：含 for 循环嵌套 if-elif-else 的函数，反编译器在函数尾生成重复的 return
或多余的 DataFrame 构造（orig=444, new=455, diff=+11）。

根因：for 循环体内 `if len(v) == N:` elif 链归约时，分支出口发射重复，
导致尾部多出 11 条指令（BUILD_LIST / LIST_EXTEND / pandas.DataFrame 重复构造）。
"""


def one_prod_to_dataframe(data):
    index = []
    columns = ['open', 'close', 'high', 'low', 'volume', 'money']
    for item in data:
        for v in item:
            if len(v) == 8:
                index.append(v)
            elif len(v) == 10:
                index.append(v)
            elif len(v) == 11:
                index.append(v)
            elif len(v) == 12:
                index.append(v)
    import pandas
    df = pandas.DataFrame(columns=columns)
    return df
