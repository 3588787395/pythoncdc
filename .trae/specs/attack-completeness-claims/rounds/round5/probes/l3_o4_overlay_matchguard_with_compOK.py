# Source Generated with Decompyle++ (Python version)
# File: l3_o4_overlay_matchguard_with_comp.pyc (Python 3.11)

__doc__ = """L3 §4 叠加攻击 (d) — match guard + with + 推导式 同函数。

关注：B61a–B61k / B122（match/guard 族）与 B70g（with 体内 if 的清理块过滤补口）、
     B151（推导式过滤项续解析）在同一函数内的优先级与叠加缺口。
"""
def o4(vals, res):
    out = []
    with res as r:
        for v in vals:
            match v:
                case [a, b] if a < b:
                    out.extend([x for x in range(a, b) if x % 2 == 0])
                    continue
                case _:
                    out.append(r)
    return out
def o4b(vals, res):
    """推导式的过滤项里带三元 + 链式比较（触及 B151 续解析与 R2 合并守卫）。"""
    out = []
    with res as r:
        for v in vals:
            match v:
                case int() if v > 0:
                    out.extend([x for x in range(v) if (x if x < 5 else -x)])
                    continue
                case _:
                    out.append(r)
    return out
