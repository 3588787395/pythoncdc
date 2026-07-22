import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR13TernaryListExtend(ExhaustiveTestCase):
    """Bug R13 (new): lst.extend((a if c else b)) — list.extend arg ternary。

    原始:
        lst.extend((a if c else b))
    缺陷: ternary 作为 list.extend 方法的位置参数。与 R12 list_extend_star
         不同：R12 测的是 list literal [*(ternary)]（LIST_EXTEND 1 在 BUILD_LIST
         0 之后），R13 测的是 list.extend(ternary)（CALL 1 调用 extend 方法）。
         验证 method call 路径的 ternary arg 归约。
    """
    SOURCE_CODE = """lst.extend((a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
