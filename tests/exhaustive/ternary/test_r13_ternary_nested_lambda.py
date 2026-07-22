import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR13TernaryNestedLambda(ExhaustiveTestCase):
    """Bug R13 (new): lambda: lambda: (a if c else b) — nested lambda ternary body。

    原始:
        lambda: lambda: (a if c else b)
    缺陷: ternary 在嵌套 lambda 的 body 中。外层 lambda 编译为外 code
         object，内层 lambda 在外层 lambda 的 code object 内作为
         MAKE_FUNCTION 指令的目标。ternary merge 块在内层 lambda 的 code
         object 中作为 RETURN_VALUE 前的栈顶。R5 已测 ternary_in_lambda
         _body_complex，R13 测 nested lambda 内 ternary 的归约路径。
    """
    SOURCE_CODE = """lambda: lambda: (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
