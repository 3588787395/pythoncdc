# Source Generated with Decompyle++ (Python version)
# File: rv6_06_withitem_deep_async.pyc (Python 3.11)

__doc__ = """rv6_06: withitem 元组/星号目标深嵌套（B33 变体）——async def 内 with (a,(b,*c)) 与嵌套星号。

对照 r6_01.w_star_unpack（扁平 (a,*rest)）/ r6_09.w_deep_unpack（(a,(b,c))）：
换宿主（async def）+ 加深嵌套（内层星号、双层元组 + 星号混合），
检验 _extract_with_items 递归绑定链解析的嵌套无感性。
"""
async def deep_tuple_star(mgr, data):
    async with mgr:
        b, *c = None
        return a + b + c[0]
async def star_mid_async(mgr, data):
    async with mgr:
        a, *rest, z = None
        return a + rest[0] + z
async def nested_star_tuple(mgr, data):
    async with mgr:
        a, *b = None
        return a + b[0] + c + d
