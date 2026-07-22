import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR13TernaryMethodChainAttr(ExhaustiveTestCase):
    """Bug R13 (new): obj.method().attr if c else obj.other — ternary with method chain。

    原始:
        obj.method().attr if c else obj.other
    缺陷: ternary 一个分支是 method chain (obj.method().attr)，另一个分支
         是 attribute access (obj.other)。R2 已测 method_chain 单纯场景，
         R13 测 method chain 作为 ternary 单一分支的复合场景。
    """
    SOURCE_CODE = """obj.method().attr if c else obj.other
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
