import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv04MultiTargetChainRhs(ExhaustiveTestCase):
    # 多目标链带复杂右值（a = b = c = d[k]）
    SOURCE_CODE = """if c:
    a = b = cc = d[k]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
