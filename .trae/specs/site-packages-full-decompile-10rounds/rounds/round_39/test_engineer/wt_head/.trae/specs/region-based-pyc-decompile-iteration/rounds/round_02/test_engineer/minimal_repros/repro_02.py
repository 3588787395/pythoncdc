# family: F2 — 类体内同名别名赋值 `X = X` 被整体丢弃
# 预期字节码模式: LOAD_NAME TickBar; STORE_NAME TickBar; LOAD_NAME BarData; STORE_NAME BarData
# 实际反编译输出: 类体里两条别名赋值全部消失，只剩 def __init__
# 关联 pyc: site-packages/IQEngine/data/data_proxy.pyc  DataProxy  baseline first_diff idx=5: LOAD_NAME TickBar -> LOAD_CONST <code object __init__>
# 判定: compile(本文件) -> decompile -> compile，递归比对所有 code object 的 co_code

class DataProxy:
    TickBar = TickBar
    BarData = BarData

    def __init__(self):
        self.a = 1
