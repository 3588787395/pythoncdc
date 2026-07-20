import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryInDictSingle(ExhaustiveTestCase):
    """Bug R2-18: 单个 ternary 作为 dict value — 字节码不一致。

    原始: d = {"a": 1 if cond else 0}
    缺陷: 单个 ternary 作为 dict value 时，BUILD_CONST_KEY_MAP 在 merge_block 中
         消费 ternary 结果。反编译器可能丢失 BUILD_CONST_KEY_MAP 结构。
    """
    SOURCE_CODE = '''d = {"a": 1 if cond else 0}'''
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
