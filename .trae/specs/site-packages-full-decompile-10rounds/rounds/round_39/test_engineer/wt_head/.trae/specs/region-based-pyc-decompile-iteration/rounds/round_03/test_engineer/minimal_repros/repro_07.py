# family: F7 — STORE_SUBSCR 的值为三元 `a if a is not None else f()` 时整条丢失（变体 1：下标赋值）
# 预期字节码模式: LOAD_FAST v; POP_JUMP_FORWARD_IF_NONE; ...; BUILD_MAP/LOAD_*/STORE_SUBSCR
# 实际反编译输出（预期）: 该三元下标赋值及后续语句被丢弃，末句被提升为 return
# 关联 pyc: 与 F7 同族（STORE_* 的值为三元时区域归约提前闭合）
# 判定: compile(本文件) -> decompile -> compile，递归比对所有 code object 的 co_code

class A:
    def __init__(self, d, k, v=None):
        self.d = {}
        self.d[k] = v if v is not None else default()
        self.register_event()
