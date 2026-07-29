"""repro_01: load_get_price Conditional+BoolOp 嵌套分支残留
区域类型: Conditional + BoolOp
违反原则: 3 (嵌套即抽象节点) + 4 (入口引用语义)
对应函数: load_get_price
缺陷镜像: `if is_utc=='0': ... elif typet==1 or typet==2 or ... ` BoolOp 链分支语句部分丢失。
  归约后父区域 then/else 引用子区域 entry，BoolOp 嵌套分支未被作为抽象节点保留。
"""


def f(panel, typet, is_utc):
    if len(panel) != 0:
        if is_utc == '0':
            panel = panel.convert('Asia/Shanghai')
            panel = panel.fillna(0)
        elif typet == 1 or typet == 2 or typet == 3 or typet == 4 or typet == 5 or typet == 13:
            panel = panel.localize('UTC').convert('Asia/Shanghai')
            panel = panel.fillna(0)
    panel = panel.localize(None)
    return panel
