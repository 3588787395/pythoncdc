import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09WalrusInSetInCond(ExhaustiveTestCase):
    # if 条件中海象+集合成员测试 if (n := x) in {1, 2, 3}:
    SOURCE_CODE = """if (n := x) in {1, 2, 3}:
    r = 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
