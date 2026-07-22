import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR13TernaryLambdaDefault(ExhaustiveTestCase):
    """Bug R13 (new): lambda x=(a if c else b): x — lambda default arg ternary。

    原始:
        lambda x=(a if c else b): x
    缺陷: ternary 作为 lambda 的默认参数值。lambda 编译时 ternary 在外层
         code object（不在 lambda code object 内），MAKE_FUNCTION 之前 ternary
         merge 块栈输出作为 default arg。R2 已测 ternary_in_default_arg
         （def f(x=ternary)），R5 已测 ternary_in_lambda_default。R13 重测
         确认 R12 修复无退化。
    """
    SOURCE_CODE = """lambda x=(a if c else b): x
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
