"""R102-02 control: dict literal already in alphabetical order.

R102-01 的控制组: 键序恰好字母序时不应触发重排。
"""


def build(data, stock, fmt):
    tem_dict = data.get(stock, {})
    if tem_dict:
        return {
            'code': stock,
            'listed_date': data[stock]['listed_date'].strftime(fmt),
            'name': data[stock]['name'],
        }
    return tem_dict
