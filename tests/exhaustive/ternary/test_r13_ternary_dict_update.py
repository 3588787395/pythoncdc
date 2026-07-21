import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR13TernaryDictUpdate(ExhaustiveTestCase):
    """Bug R13 (new): d.update((a if c else b)) — dict.update arg ternary。

    原始:
        d.update((a if c else b))
    缺陷: ternary 作为 dict.update 方法的位置参数。与 R12 dict_merge_double_star
         不同：R12 测的是 dict literal {**(ternary)}（DICT_UPDATE 1 在 BUILD_MAP
         0 之后），R13 测的是 dict.update(ternary)（CALL 1 调用 update 方法）。
    """
    SOURCE_CODE = """d.update((a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
