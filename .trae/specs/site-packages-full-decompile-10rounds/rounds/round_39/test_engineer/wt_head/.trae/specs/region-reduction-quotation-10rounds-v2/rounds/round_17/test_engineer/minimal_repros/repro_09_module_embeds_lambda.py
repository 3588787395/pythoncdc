"""复现 09：模块嵌入 lambda code 对象 — 传递性不一致变体。

模式：<module> 不仅嵌入顶层函数，也可能嵌入 lambda/listcomp 等 code 对象。
在 quotation.pyc 中，<module> 的 133 个嵌入对象全部是顶层函数（co_name 为函数名）。
lambda/listcomp 通常嵌套在函数内部（walk_code 键为 func.<lambda>），不直接出现在
<module> 的 LOAD_CONST 中。因此委托机制对 <module> 仅需检查 co_name 是否为
顶层函数键（co_name in results），天然排除嵌套 lambda/listcomp。

本复现演示：module 级 lambda 作为顶层对象，其 co_name=<lambda>，walk_code 键=<lambda>。
若独立比较过，则委托生效。
"""
# 模块级 lambda（co_name='<lambda>'）
process = lambda x: x + 1
