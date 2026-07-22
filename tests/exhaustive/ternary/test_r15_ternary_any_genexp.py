import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernaryAnyGenexp(ExhaustiveTestCase):
    """Bug R15 (new): any((a if c else b) for x in y) — any + genexp 内 ternary。

    原始:
        any((a if c else b) for x in y)
    缺陷: ternary 作为 genexp 的 elt 表达式，genexp 作为 any 的单参数。
         字节码：PUSH_NULL + LOAD any + LOAD_CONST <genexp code> + MAKE_FUNCTION
         + GET_ITER + PRECALL + CALL 1。ternary 在 genexp 内部 code object，
         应由 _build_function_def 嵌套递归处理。R5 已测 ternary_in_genexp
         单独 genexp，R15 测 any + genexp + ternary 组合。
    """
    SOURCE_CODE = """any((a if c else b) for x in y)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
