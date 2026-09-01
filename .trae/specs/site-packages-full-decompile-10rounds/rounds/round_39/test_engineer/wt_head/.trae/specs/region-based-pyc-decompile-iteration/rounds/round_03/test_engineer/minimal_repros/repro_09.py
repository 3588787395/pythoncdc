# family: F8 — if 块内 import 后跟普通赋值（变体 1：去除嵌套 if 与 or）
# 预期字节码模式: if cond: import ptvsd; self.x = 1
# 实际反编译输出（预期）: 赋值被提到 import 之前，插入 return None，import 变不可达
# 关联 pyc: site-packages/IQEngine/plugins/plugin_system_debug/__init__.pyc setup（F8）
# 判定: compile(本文件) -> decompile -> compile，递归比对所有 code object 的 co_code

def setup(self, engine):
    if engine.debug:
        import ptvsd
        self.x = 1
