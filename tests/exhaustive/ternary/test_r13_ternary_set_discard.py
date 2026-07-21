import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR13TernarySetDiscard(ExhaustiveTestCase):
    """Bug R13 (new): s.discard((a if c else b)) — set.discard arg ternary。

    原始:
        s.discard((a if c else b))
    缺陷: ternary 作为 set.discard 方法的位置参数。与 set.add 同模式但
         语义不同（discard 用于删除元素）。验证 method call 路径与 add
         完全一致，仅方法名不同。验证 ternary 在 set.discard arg 位置。
    """
    SOURCE_CODE = """s.discard((a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
