# repro_06: try 体内 if/elif/else 链 + 仅 finally（无 except）
# 缺陷类型: try-finally 结构反编译，try 体内容丢失
# 预期行为: 反编译后字节码一致；try 体丢失则触发缺陷。
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
    finally:
        globals()['r6'] = flag
    return flag
