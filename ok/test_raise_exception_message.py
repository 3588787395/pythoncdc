"""测试raise异常消息问题"""

def func():
    # 原始代码可能是：raise ValueError('您输入的行情数据字段有误')
    # 但反编译器错误地生成了：raise '您输入的行情数据字段有误'()
    raise ValueError('您输入的行情数据字段有误')
