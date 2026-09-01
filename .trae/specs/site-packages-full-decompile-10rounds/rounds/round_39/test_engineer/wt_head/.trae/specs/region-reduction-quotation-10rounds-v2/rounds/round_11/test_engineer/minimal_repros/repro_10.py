"""repro_10: load_get_price Conditional+BoolOp 多层嵌套综合 (if/elif/or/in 混合)
区域类型: Conditional + BoolOp
违反原则: 3 (嵌套即抽象节点) + 4 (入口引用语义)
对应函数: load_get_price
缺陷镜像: 综合复现 `if cond or cond: if _typet in (7,8,9,15): if is_utc=='0' or typet==1: ...
  elif typet==2 or typet==3: ... else: ...` 多层 Conditional+BoolOp 嵌套。
  归约后父区域 then/else 引用子区域 entry 而非全部块，BoolOp 链分支与条件入口
  跳转目标残留(嵌套即抽象节点 / 入口引用语义未对齐)。
"""


def f(panel, typet, is_utc, _typet):
    if len(panel) != 0 or is_utc is not None:
        if _typet in (7, 8, 9, 15):
            if is_utc == '0' or typet == 1:
                panel = panel.convert('Asia/Shanghai')
            elif typet == 2 or typet == 3:
                panel = panel.localize('UTC')
            else:
                panel = panel.fillna(0)
        else:
            panel = panel.fillna(0)
    return panel
