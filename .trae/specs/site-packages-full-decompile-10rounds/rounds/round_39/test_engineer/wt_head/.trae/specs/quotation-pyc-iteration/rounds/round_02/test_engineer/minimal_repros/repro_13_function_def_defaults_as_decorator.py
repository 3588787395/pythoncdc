"""
Defect 13 (R2 新增) — FUNCTION_DEF：无装饰器的函数 defaults 元组被误发射为 `@((...))` 装饰器
================================================================
R1 关联：repro_03_function_def_list_default（R1 已修复列表默认值丢失；
疑似 R1 对 `_generate_arguments` 默认值渲染的改动引入本回归）。

R2 复现状态：**新出现（3 处）**。
  quotation.pyc R2 产物：
    line 755  `@((None, None, 'daily', None, None, None, False))`        → get_price 后
    line 767  `@(('1d', None, None, None, False, False, None, 'nan', False))`  → get_history 前
    line 2151 `@((None, None, None, None, None, None, None, None, 1, True, False))` → get_fundamentals 前
  —— 这三个 `@((...))` 恰为紧随其后的函数（get_price / get_history / get_fundamentals）
     的位置参数默认值元组。原 pyc 中这些函数均无装饰器，MAKE_FUNCTION 的 defaults
     元组被错误发射为独立的装饰器表达式，且默认值未出现在函数签名中。

触发区域类型：FUNCTION_DEF (MAKE_FUNCTION defaults)
根因初判：
    `core/cfg/code_generator.py::_generate_function_def` / `_generate_arguments`
    在函数无装饰器但含 defaults 元组时，把 defaults 元组作为前导装饰器表达式
    `@((...))` 发射，而非填入函数签名的 `name=default`。疑似 R1 对
    repro_03 默认值渲染路径改动后，defaults 节点在无装饰器分支被误挂到
    decorators 列表。
    违反「每块唯一归属」：defaults 元组应归函数签名，不应归 decorators。

最小字节码模式（Python 3.11，模块级 MAKE_FUNCTION with defaults, no decorator）：
    LOAD_CONST ('1d', None, None, None, False, False, None, 'nan', False)  # defaults 元组
    LOAD_CONST <code get_history>
    MAKE_FUNCTION defaults
    STORE_NAME get_history
    → R2 误发射：@(('1d', None, ...)) \n def get_history(...): ...

R2 反编译产物（错误）：
    @(('1d', None, None, None, False, False, None, 'nan', False))
    def get_history(count, frequency='1d', field=None, security_list=None, fq=None, skip_suspended=False, include=False, query_date=None, fill='nan', is_dict=False):
        ...
期望产物：
    def get_history(count, frequency='1d', field=None, security_list=None, fq=None, skip_suspended=False, include=False, query_date=None, fill='nan', is_dict=False):
        ...

验证：python pycdc.py <this>.pyc  # 观察 defaults 元组被发射为 @((...)) 装饰器
"""
def get_history(count, frequency='1d', field=None, security_list=None, fq=None, skip_suspended=False, include=False, query_date=None, fill='nan', is_dict=False):
    ClearAllCache()
    if count <= 0:
        log.error('count error')
    return count
