"""R8 repro_06: load_get_price 嵌套 if 含 BoolOp 链语句丢失。
缺陷: `if is_utc == '0':` 分支下的 `elif typet == 1 or typet == 2 or ...` BoolOp 链所在分支语句丢失，导致 -26 指令差异。
区域类型: Conditional + BoolOp  违反原则: 3(嵌套即抽象节点)
"""
def f(panel, typet, is_utc):
    if len(panel) != 0:
        if is_utc == '0':
            panel = panel.convert('Asia/Shanghai')
        elif typet == 1 or typet == 2 or typet == 3 or typet == 4 or typet == 5 or typet == 13:
            panel = panel.localize('UTC').convert('Asia/Shanghai')
    panel = panel.localize(None)
    return panel
