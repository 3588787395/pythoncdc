# rv8_03: B55 分支 A/B 判据面变体攻击 —— except 段内 return None + 尾随语句 / try 体 return 后接 except 段语句
# 判据边界：_b55_is_try_handler_exit_trailing_return 的 (2) 单前驱互斥（共享
# 收尾块形态不得豁免）+ return_succ 裸 return 判据对「except 段内显式
# return None 后尾随语句」的幻影豁免面。


def except_return_none_then_trailing(x):
    try:
        v = int(x)
    except ValueError:
        print('bad')
        return None
    return v + 1


def except_pass_trailing_implicit(x):
    try:
        v = int(x)
    except ValueError:
        pass
    return v


def two_handlers_shared_tail(x):
    try:
        v = int(x)
    except ValueError:
        v = 0
    except TypeError:
        v = 1
    return v


def try_body_return_then_except(x):
    try:
        return 1
    except ValueError:
        return 2


def handler_return_value_then_trailing(x):
    try:
        v = int(x)
    except ValueError:
        return 0
    except TypeError:
        return None
    return v
