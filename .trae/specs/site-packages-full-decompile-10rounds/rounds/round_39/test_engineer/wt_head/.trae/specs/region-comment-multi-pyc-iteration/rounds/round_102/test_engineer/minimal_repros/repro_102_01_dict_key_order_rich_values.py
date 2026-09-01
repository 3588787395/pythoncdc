"""R102-01: dict literal with non-alphabetical source key order + rich value exprs.

fly_data_source.get_stock_info 同型: 反编译产物疑似将 dict 字面量
按键名字母序重排 ('listed_date' 先于 'name' 发射)。
"""


def build(data, stock, fmt):
    tem_dict = data.get(stock, {})
    if tem_dict:
        return {
            'name': data[stock]['name'],
            'listed_date': data[stock]['listed_date'].strftime(fmt),
            'code': stock,
        }
    return tem_dict
