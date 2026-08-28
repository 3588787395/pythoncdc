# family: F3 — 连续多条 `obj.attr = a or b.c` — 第二条起被截断为裸表达式，后续语句全部丢失
# 预期字节码模式: 第 2 条: LOAD_FAST b; JUMP_IF_TRUE_OR_POP; LOAD_FAST env; LOAD_ATTR b; ... STORE_ATTR y
# 实际反编译输出: 第 2 条退化成裸表达式 `b`，`return o` 变成 `return env.b`
# 关联 pyc: site-packages/IQEngine/account/trade.pyc  create_trade  baseline first_diff idx=16 (orig 68 -> decomp 19)
# 判定: compile(本文件) -> decompile -> compile，递归比对所有 code object 的 co_code

def f(o, a, b, c, env):
    o.x = a or env.a
    o.y = b or env.b
    o.z = c
    return o
