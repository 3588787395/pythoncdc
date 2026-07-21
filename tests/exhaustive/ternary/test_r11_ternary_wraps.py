import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR11TernaryFunctoolsWraps(ExhaustiveTestCase):
    """Bug R10-10 (re-verify in R11): functools.wraps + ternary in *args.

    原始:
        from functools import wraps
        def deco(f):
            @wraps(f)
            def g(*args, **kwargs):
                return f(*(args if c else ()), **kwargs)
            return g
    缺陷: @wraps(f) 装饰器 + ternary in *args of function call。ternary 表达式
         (args if c else ()) 作为 *args 的实参，merge 块是 CALL_FUNCTION_EX 的
         *args 参数。@wraps(f) 调用栈帧 PUSH_NULL + LOAD_NAME wraps + LOAD_NAME f
         + PRECALL + CALL + LOAD_CONST g_code + MAKE_FUNCTION + PRECALL + CALL +
         STORE_NAME g。
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
