# Source Generated with Decompyle++ (Python version)
# File: l3_g3_r4_await_asyncwith_finally.pyc (Python 3.11)

__doc__ = """L3 §3 通用性抽检 — 族 R4（await 挂起链族）。

新构型（非语料）：
  `await` 出现在 **async with 体内**，且 `finally` 内另有一次 `await`；
  已落地的 B47（三元臂值 await）、B112（上一显著操作码 / GET_AITER 判别）、
  B128（await setup 结果是否被 IfRegion 条件消费）均未覆盖「await 位于
  async-with 清理链 / finally 内」这一形态。
判据问题：B112 的「上一显著操作码跳过 PRECALL/CACHE」判据在 async-with
  体内是否仍成立？await 位于 finally 内时挂起点是否仍被正确归约？
"""
async def r4_asyncwith(res):
    out = []
    async with res as r:
        try:
            out.append(await r.read())
        finally:
            pass
        out.append(await r.flush())
    return out
async def r4_await_in_for(xs, res):
    out = []
    for x in xs:
        v = await res.get(x)
    return out
