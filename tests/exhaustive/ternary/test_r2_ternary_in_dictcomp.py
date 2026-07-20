import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryInDictcomp(ExhaustiveTestCase):
    """Bug R2-31: ternary 在 dict comprehension 中 — 字节码不一致。

    原始: d = {k: (v if cond else 0) for k, v in items}
    缺陷: ternary 在 dictcomp value 中时，MAP_ADD 在 merge_block 中消费
         ternary 结果。反编译器可能丢失 dictcomp 结构。
    """
    SOURCE_CODE = """d = {k: (v if cond else 0) for k, v in items}"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
