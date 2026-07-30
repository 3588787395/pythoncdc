# repro_09: 嵌套 try（外层 try 包内层 try/except），内层 try 体含 if/elif/else
# 缺陷类型: 嵌套 try/except 结构反编译，内层 try 体丢失
# 预期行为: 反编译后字节码一致；内层 try 体丢失则触发缺陷。
import sys


def f():
    flag = '0'
    try:
        try:
            if sys.version_info[0] == 3 and sys.version_info[1] == 11:
                flag = '3.11'
            elif sys.version_info[0] == 3 and sys.version_info[1] == 5:
                flag = '3.5'
            else:
                print('unsupported')
        except AttributeError:
            flag = 'inner'
    except:
        flag = 'outer'
    return flag
