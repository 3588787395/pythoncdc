"""repro_03: if-continue 兄弟语句 — 内层 if 无 else（纯 continue 回边）。

测试 aspect: 内层 if 无 else 分支，false 分支直接跳到回边（JUMP_BACKWARD）。
true 分支 fallthrough 到回边。两分支均→回边，continue 无条件。

重点验证：反编译器不可将内层 if 的 false 分支误判为跳到 post-loop（break 语义），
而应识别 false 分支→回边（continue 语义），生成 continue 兄弟语句。

    for j in range(n):
        if outer_cond:
            if inner_cond:      # 无 else
                x = 1
            continue            # ← false 分支也→此处（回边）
        y = j
        break
"""


def f(data):
    output = []
    for j in range(len(data)):
        if data[j] is not None:
            if data[j] > 10:
                output.append(data[j])
            continue
        output.append(0)
        break
    return output
