# repro_02: try 体内 if/elif/else 链 + except Exception as e + finally（带 as 绑定）
# 缺陷类型: try 体内容丢弃 + except as 绑定结构反编译
# 预期行为: 反编译后字节码一致；try 体丢失或 as 绑定错误则触发缺陷。
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
    except Exception as e:
        flag = 'err:' + str(e)
    finally:
        globals()['r2'] = flag
    return flag
