# Source Generated with Decompyle++ (Python version)
# File: l3_g4_r5_match_mapping_star_guard.pyc (Python 3.11)

__doc__ = """L3 §3 通用性抽检 — 族 R5（match-with 幻影族 / 模式解析）。

新构型（非语料）：
  mapping 模式 + `**rest` + sequence 子模式（含 `*star`）+ **guard** 组合；
  已落地的 B61a–B61k / B122 覆盖 or 守卫臂链、类模式双 COPY、嵌套字面量链等，
  但未覆盖「mapping 模式内的 sequence 子模式 + star + guard」这一组合。
判据问题：B122 的「模式比较材料隔离 / 入口同块去重」判据是否与具体模式形状
  （literal / class）绑定？guard 提取是否对 mapping 模式内的子模式同样成立？
"""
def r5_match(v):
    match v:
        case {'k': [a, *rest]} if a > 0:
            return (a, rest)
        case [x, *ys] if x:
            return (x, ys)
        case _:
            pass
def r5_match_mapping(v):
    match v:
        case {'a': p, **rest}:
            return (p, rest)
        case {'b': q}:
            return q
        case other:
            return other
