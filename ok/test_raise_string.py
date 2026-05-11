"""测试raise字符串问题"""

def func():
    # 原始代码可能是：raise '您输入的行情数据字段有误'
    # 这看起来像是反编译器错误地处理了raise语句
    raise ValueError('您输入的行情数据字段有误')
