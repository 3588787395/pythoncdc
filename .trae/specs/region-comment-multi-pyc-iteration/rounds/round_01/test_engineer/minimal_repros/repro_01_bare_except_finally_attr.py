# repro_01: try 体内含 if/elif/else 链 + 裸 except + finally（最接近原 pyc 缺陷）
# 缺陷类型: try/except/finally 反编译时 try 体内的 if/elif/else 链被丢弃（坍缩为 pass）
# 预期行为: 反编译后字节码应与原字节码一致；若 try 体被替换为 pass 则触发缺陷。
import sys


def get_ver():
    flag = '0'
    try:
        if sys.version_info[0] == 3 and sys.version_info[1] == 11:
            flag = '3.11'
        elif sys.version_info[0] == 3 and sys.version_info[1] == 5:
            flag = '3.5'
        else:
            print('unsupported')
    except:
        pass
    finally:
        globals()['ver'] = flag
    return flag
