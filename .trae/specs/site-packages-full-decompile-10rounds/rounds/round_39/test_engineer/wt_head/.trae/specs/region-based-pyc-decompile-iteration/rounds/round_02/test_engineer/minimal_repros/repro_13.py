# family: F8 — F8 的语句重排形式：if 块内 import 与其后的 `or` 赋值被交换顺序，并插入 return None
# 预期字节码模式: import 在最前，随后 if/嵌套 if，最后 engine.config... = config.timeout or 10
# 实际反编译输出: 赋值被提到 import 之前，紧跟 `return None`，import 及其后语句变成不可达代码
# 关联 pyc: site-packages/IQEngine/plugins/plugin_system_debug/__init__.pyc  setup（真实输出即 `... = config.timeout or 10` + `return None` + `import ptvsd`）
# 判定: compile(本文件) -> decompile -> compile，递归比对所有 code object 的 co_code

def setup(self, engine):
    if engine.config.other.enable_debug:
        import ptvsd
        if get_python_version() == '3.11':
            ptvsd.reset()
        engine.config.other.enable_debug = config.timeout or 10
