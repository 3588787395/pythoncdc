import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09SetInCond(ExhaustiveTestCase):
    # if 条件含集合成员测试 x in {1,2,3} or y in {4,5}
    SOURCE_CODE = """if x in {1, 2, 3} or y in {4, 5}:
    r = 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
