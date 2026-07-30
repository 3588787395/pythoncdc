# repro_08: except Exception + finally（try 体含 if/elif/else 链，最接近原 pyc）
# 缺陷类型: try 体内 if/elif/else 链 + except + finally，try 体被丢弃
# 预期行为: 反编译后字节码一致；try 体被替换为 pass 则触发缺陷（对应原 pyc 缺陷）。
import sys


def get_python_version():
    import traceback
    flag = '0'
    try:
        if sys.version_info[0] == 3 and sys.version_info[1] == 11:
            flag = '3.11'
        elif sys.version_info[0] == 3 and sys.version_info[1] == 5:
            flag = '3.5'
        else:
            print('unsupported')
    except Exception:
        traceback.print_exc()
    finally:
        globals()['python_version'] = flag
    return flag
