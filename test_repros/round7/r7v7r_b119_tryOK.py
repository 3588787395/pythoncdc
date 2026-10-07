# Source Generated with Decompyle++ (Python version)
# File: r7v7r_b119_try.pyc (Python 3.11)

__doc__ = """Round 7 复核批变体探针（r7v7r_*）——B119 守卫变体面。

评审工程师独立攻击（任务 7.3）：验证收紧⑥（吞没风险事实）与镜像
守卫的触发边界（全 MATCH 预期）：
- b119r_merge_in_generating_try：if 的 merge 位于**尚未完成生成**的
  TryExceptRegion 块集内（普通 try 体内 if + 尾随语句）——条件⑥必须
  拦住（提前发射会同子 try 收尾时序冲突）；
- b119r_merge_no_try：merge 是 BoolOp/普通汇合块（不在任何 try 块集
  内，n7_01/neg_simple_and_or 家族变体）——条件⑥必须拦住；
- b119r_return_in_try_if：try 体内 if 真臂 return（g_in_try_except
  家族变体）——条件⑥必须拦住；
- b119r_real_body_tryfin：try 体含可抛用户语句的真实 try/finally
  （有独立 finally_copy_blocks/块切分）——镜像守卫必须不触发。
"""
DEFAULT_MAP = {'a': 1}
def b119r_merge_in_generating_try(d, flag):
    try:
        if flag:
            d['a'] = 1
        d['b'] = 2
    except KeyError:
        pass
    return d
def b119r_merge_in_generating_try_deep(d, flag, gate):
    if gate:
        try:
            if flag:
                d['a'] = 1
            d['b'] = 2
        except KeyError:
            pass
    return d
def b119r_merge_no_try(a, b, flag):
    if flag:
        return a or b
    else:
        return -1
def b119r_merge_no_try_deep(a, b, flag, gate):
    if gate and flag:
        return a or b
    return -1
def b119r_return_in_try_if(cache, key, flag):
    try:
        if flag:
            return cache[key]
    except KeyError:
        return -1
    return 0
def b119r_return_in_try_if_deep(cache, key, flag, gate):
    if gate:
        try:
            if flag:
                return cache[key]
        except KeyError:
            return -1
    return 0
def b119r_real_body_tryfin(items):
    out = []
    try:
        for x in items:
            out.append(x)
    finally:
        out.append(len(out))
    return out
def b119r_real_body_tryfin_deep(items, flag):
    out = []
    if flag:
        try:
            for x in items:
                out.append(x)
        finally:
            out.append(len(out))
    return out
