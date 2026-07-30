# repro_05: try 体内 if/elif/else 链 + except/else/finally
# 缺陷类型: try 体内容丢弃 + else 子句反编译
# 预期行为: 反编译后字节码一致；try 体或 else 体丢失则触发缺陷。
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
    except Exception:
        flag = 'err'
    else:
        flag = flag + '!ok'
    finally:
        globals()['r5'] = flag
    return flag
