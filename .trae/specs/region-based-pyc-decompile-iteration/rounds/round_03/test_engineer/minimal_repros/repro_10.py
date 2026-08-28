# family: F8 — if/elif 块内 import（变体 2：验证 elif 分支内的 import 是否同样退化）
# 预期字节码模式: if cond: import a; elif other: import b
# 实际反编译输出（预期）: import 退化成 `x = None` 且插入 return None
# 关联 pyc: 与 F8 同族（if 块内 IMPORT_NAME 还原失败）
# 判定: compile(本文件) -> decompile -> compile，递归比对所有 code object 的 co_code

def setup(self, engine):
    if engine.debug:
        import ptvsd
        self.x = 1
    elif engine.trace:
        import remote_pdb
        self.y = 2
