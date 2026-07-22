import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR11TernaryFunctoolsCache(ExhaustiveTestCase):
    """Bug R11 (new): functools.cache + ternary in body.

    原始:
        from functools import cache
        @cache
        def fib(n):
            return (n if n < 2 else fib(n - 1) + fib(n - 2))
    缺陷: @cache 装饰器 + 递归 ternary return。ternary body 是 fib(n-1) +
         fib(n-2)（CALL + BINARY_OP），orelse 是 n。cond_block 含 LOAD_FAST n +
         LOAD_CONST 2 + COMPARE_OP <，merge 块 RETURN_VALUE 是 Return(IfExp)。
         递归调用 fib 在 ternary body 内可能暴露 ternary consumer + 递归 Call
         的归属冲突。
    """
    SOURCE_CODE = """from functools import cache
@cache
def fib(n):
    return (n if n < 2 else fib(n - 1) + fib(n - 2))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
