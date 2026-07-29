"""复现 02：模块嵌入 instr_diff 函数 — 传递性不一致。

模式：<module> 嵌入 change_his_to_backward 的 code 对象。
该函数指令数相同（578 vs 578）但 @idx296 指令内容不同（POP_JUMP 目标不同）。
<module> 自身指令全部正确，但因嵌入的 code 对象递归比较时 instr_diff 而失败。

对应：<module> @idx453 (LOAD_CONST <code change_his_to_backward>)。
"""
def helper(data):
    # 模拟 change_his_to_backward：指令数相同但内容不同（instr_diff）
    result = []
    for item in data:
        if item is not None:
            result.append(item)
        else:
            result.append(None)
    return result
