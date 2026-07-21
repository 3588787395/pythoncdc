import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR13TernaryCallStarArgs(ExhaustiveTestCase):
    """Bug R13 (new): print(*(a if c else b)) — ternary as *args in call。

    原始:
        print(*(a if c else b))
    缺陷: ternary 作为 print 函数调用的 *args 展开位置。CALL_FUNCTION_EX 路径
         而非 CALL kwarg 路径。ternary merge 块栈输出通过 BUILD_TUPLE_N 等被
         unpack 为 *args。R8 已测 ternary_starred_call 但 R13 重测确认 R12
         修复无退化，并测 print 内置函数变体（receiver 是 builtin 而非普通函数）。
    """
    SOURCE_CODE = """print(*(a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
