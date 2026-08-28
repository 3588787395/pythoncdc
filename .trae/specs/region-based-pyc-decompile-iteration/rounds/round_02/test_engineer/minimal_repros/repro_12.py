# family: F8 — if 块内的 `import x` 被还原成 `x = None`（IMPORT_NAME 的 level 常量丢失）
# 预期字节码模式: LOAD_CONST 0; LOAD_CONST None; IMPORT_NAME ptvsd; STORE_FAST ptvsd
# 实际反编译输出: ptvsd = None（并且重复一次），末尾还多出 return None
# 关联 pyc: site-packages/IQEngine/plugins/plugin_system_debug/__init__.pyc  setup  baseline first_diff idx=5 (orig 115 -> decomp 18)
# 判定: compile(本文件) -> decompile -> compile，递归比对所有 code object 的 co_code

def f(engine):
    if engine.debug:
        import ptvsd
        engine.x = ptvsd.y() or 10
        engine.z = 1
