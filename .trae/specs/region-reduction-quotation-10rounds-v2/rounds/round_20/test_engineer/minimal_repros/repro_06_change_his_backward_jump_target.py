"""repro_06: change_his_to_backward 跳转目标偏移 — POP_JUMP_IF_NOT_NONE 目标差异。

change_his_to_backward @idx296 的 POP_JUMP_FORWARD_IF_NOT_NONE 在 orig 跳到 330
（else 分支入口），new 跳到 342（else 分支内重排后的不同入口）。这不是 elif 链归一化
可覆盖的差异（现有 _jump_targets_equiv 仅处理 elif 链 fall-forward），而是 else 分支
内部指令顺序重排导致的目标偏移。

后续迭代建议：code_generator 对齐 if/else 跳转目标布局，无法在 exact_match_stats
安全归一化（会掩盖真实指令重排差异）。
"""


def f(x, y):
    if x is not None:
        a = x + 1
        b = a * 2
    else:
        if y != 0:
            y = 0
        c = y + 1
    return y
