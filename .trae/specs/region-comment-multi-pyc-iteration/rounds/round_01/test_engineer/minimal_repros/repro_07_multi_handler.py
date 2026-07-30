# repro_07: try 体内 if/elif/else 链 + 多 handler（except A + except B）+ finally
# 缺陷类型: try 体内容丢弃 + 多 handler 反编译
# 预期行为: 反编译后字节码一致；try 体或某个 handler 丢失则触发缺陷。
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
    except TypeError:
        flag = 'type'
    except AttributeError:
        flag = 'attr'
    finally:
        globals()['r7'] = flag
    return flag
