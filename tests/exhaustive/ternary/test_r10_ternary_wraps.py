import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR10TernaryFunctoolsWraps(ExhaustiveTestCase):
    """Bug R10: functools.wraps + ternary in body — 字节码不一致。

    原始:
        from functools import wraps
        def deco(f):
            @wraps(f)
            def g(*args, **kwargs):
            return f(*(args if c else ()), **kwargs)
        return g
    缺陷: @wraps(f) 装饰器 + ternary in *args of function call。ternary
         表达式 (args if c else ()) 作为 *args 的实参，merge 块是
         CALL_FUNCTION_EX 的 *args 参数。@wraps(f) 调用栈帧 PUSH_NULL +
         LOAD_NAME wraps + LOAD_NAME f + PRECALL + CALL + LOAD_CONST g_code
         + MAKE_FUNCTION + PRECALL + CALL + STORE_NAME g。依「父引用子入口」：
         @wraps Call 通过 MAKE_FUNCTION 之后的 CALL 引用 FunctionObject；
         f(*args) Call 通过 cond_block 的 f 入口 + merge_block 的
         CALL_FUNCTION_EX 引用 ternary 子节点作为 *args。
    """
    SOURCE_CODE = """from functools import wraps
def deco(f):
    @wraps(f)
    def g(*args, **kwargs):
        return f(*(args if c else ()), **kwargs)
    return g
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
