"""repro_09: 复现 get_str_data 反编译缺陷（for 循环体截断 + 尾部代码丢失 -48）。

缺陷模式：
    for stock in rdata.items(): ...
    # 尾部 pandas.Panel 构造丢失
循环后 pandas.Panel(data) 构造在 FOR_ITER 边界处被截断（orig=317, new=269, diff=-48）。

根因：FOR_ITER 边界提前收敛，循环后 pandas.Panel 构造语句未被纳入函数体尾部，
tail code 全部丢失。
"""


def get_str_data(rdata):
    data = {}
    for stock in rdata.items():
        code = stock[0]
        values = stock[1]
        data[code] = values
    import pandas
    panel = pandas.Panel(data)
    return panel
