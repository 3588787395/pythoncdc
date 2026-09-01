"""复现 01：模块嵌入 len_diff 函数 — 传递性不一致。

模式：<module> 通过 LOAD_CONST 嵌入 get_str_data 的 code 对象。
原始版本 get_str_data 有 317 条指令，反编译产物仅 269 条（len_diff -48）。
<module> 自身 1023 条指令全部正确，但因嵌入 get_str_data 的 code 对象递归比较时
长度不等而失败。这是传递性不一致：get_str_data 的不一致已在独立比较中计入，
不应在 <module> 中重复计入。

对应：<module> @idx444 (LOAD_CONST <code get_str_data>)。
"""
def helper(x):
    # 模拟 get_str_data：原始版本有更多指令（len_diff）
    a = str(x)
    b = a + "_suffix"
    c = b.upper()
    return c
