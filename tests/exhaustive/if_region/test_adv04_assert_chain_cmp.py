import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv04AssertChainCmp(ExhaustiveTestCase):
    # 复合条件 assert（链式比较作 assert 条件）
    SOURCE_CODE = """if c:
    assert 0 < a < 10"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
