# repro_12: try 体内 if/elif/else 链 + 函数调用 + except + finally
# 缺陷类型: try 体含函数调用反编译，try 体内容丢失
# 预期行为: 反编译后字节码一致；try 体被替换为 pass 则触发缺陷。
import sys


def _helper(a, b):
    return a + b


def f():
    flag = '0'
    try:
        if sys.version_info[0] == 3 and sys.version_info[1] == 11:
            flag = '3.11'
        elif sys.version_info[0] == 3 and sys.version_info[1] == 5:
            flag = '3.5'
        else:
            x = _helper(1, 2)
            flag = str(x)
    except Exception:
        flag = 'err'
    finally:
        globals()['r12'] = flag
    return flag
