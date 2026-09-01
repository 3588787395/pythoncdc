# repro_03: try 体内 if/elif/else 链 + except 多异常类型元组 + finally
# 缺陷类型: try 体内容丢弃 + 多异常类型元组 handler 反编译
# 预期行为: 反编译后字节码一致；try 体丢失或元组 handler 错误则触发缺陷。
import sys


def f():
    flag = '0'
    try:
        if sys.version_info[0] == 3 and sys.version_info[1] == 11:
            flag = '3.11'
        elif sys.version_info[0] == 3 and sys.version_info[1] == 5:
            flag = '3.5'
        else:
            print('unsupported')
    except (TypeError, ValueError, AttributeError):
        flag = 'tuple_err'
    finally:
        globals()['r3'] = flag
    return flag
