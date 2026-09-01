# repro_10: try 中含 return
# 缺陷类型: try 体含 return 语句反编译，try 体/return 丢失
# 预期行为: 反编译后字节码一致；return 丢失或 try 体错误则触发缺陷。
def f():
    try:
        return 1
    except:
        return 2
