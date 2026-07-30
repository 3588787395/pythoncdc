# repro_04: try 体内 if/elif/else 链 + 裸 except（无 finally）
# 缺陷类型: try 体内容丢弃 + 裸 except handler 反编译
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
    except:
        flag = 'err'
    return flag
