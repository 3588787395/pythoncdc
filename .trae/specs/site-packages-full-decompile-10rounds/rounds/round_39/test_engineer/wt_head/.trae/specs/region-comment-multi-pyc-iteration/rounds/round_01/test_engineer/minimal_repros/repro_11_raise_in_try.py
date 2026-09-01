# repro_11: try 体内 if/elif/else 链 + raise + except + finally
# 缺陷类型: try 体含 raise 语句反编译，try 体/raise 丢失
# 预期行为: 反编译后字节码一致；raise 丢失或 try 体错误则触发缺陷。
import sys


def f():
    flag = '0'
    try:
        if sys.version_info[0] == 3 and sys.version_info[1] == 11:
            flag = '3.11'
        elif sys.version_info[0] == 3 and sys.version_info[1] == 5:
            raise ValueError('unsupported old')
        else:
            print('unsupported')
    except ValueError:
        flag = 'caught'
    finally:
        globals()['r11'] = flag
    return flag
