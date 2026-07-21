import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR11TernaryLruCache(ExhaustiveTestCase):
    """Bug R11 (new): functools.lru_cache + ternary in body.

    原始:
        from functools import lru_cache
        @lru_cache(maxsize=128)
        def f(x):
            return (x * 2 if c else x)
    缺陷: @lru_cache(maxsize=128) 带参装饰器 + ternary return。装饰器调用栈
         PUSH_NULL + LOAD_NAME lru_cache + KW_NAMES + LOAD_CONST 'maxsize' +
         LOAD_CONST 128 + PRECALL + CALL + LOAD_CONST f_code + MAKE_FUNCTION +
         PRECALL + CALL + STORE_NAME f。f 的 code object 内 ternary merge
         块 RETURN_VALUE 是 Return(IfExp)。
    """
    SOURCE_CODE = """from functools import lru_cache
@lru_cache(maxsize=128)
def f(x):
    return (x * 2 if c else x)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
