"""repro_08: 复现 load_get_price 反编译缺陷（if 分支目标计算过短 -25）。

缺陷模式：
    if len(panel.major_axis) != 0:
        if is_utc == '0': ...
        elif typet in (...): ...
    其中 POP_JUMP_FORWARD_IF_FALSE 目标计算过短，导致 if 分支体被截断
（orig=226, new=201, diff=-25）。

根因：外层 if 的 POP_JUMP_FORWARD_IF_FALSE 跳转目标计算过短，elif 链的后续分支
体在跳转目标处被截断。R3 长 or 链修复未触达该原始 CFG 路径。
"""


def load_get_price(panel, is_utc, typet):
    if len(panel) != 0:
        if is_utc == '0':
            x = 1
        elif typet in ('1', '2', '3'):
            x = 2
        else:
            x = 3
    return x
