import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv04WalrusConstMatch(ExhaustiveTestCase):
    # walrus 绑定常量值并作比较：是否触发 match 误判
    SOURCE_CODE = """if (n := 1) > 0:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
