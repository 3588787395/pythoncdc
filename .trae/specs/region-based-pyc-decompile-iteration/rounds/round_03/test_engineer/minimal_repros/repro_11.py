# family: F2 — 类体内单条同名别名赋值 `X = X` 被丢弃（变体：只有一条，验证是否依赖「多条成对」才触发）
# 预期字节码模式: LOAD_NAME X; STORE_NAME X; 随后 def m
# 实际反编译输出（预期）: 别名赋值消失，只剩 def m
# 关联 pyc: site-packages/IQEngine/data/data_proxy.pyc DataProxy（F2，类体 `TickBar = TickBar; BarData = BarData`）
# 判定: compile(本文件) -> decompile -> compile，递归比对所有 code object 的 co_code

class C:
    X = X

    def m(self):
        return 1
