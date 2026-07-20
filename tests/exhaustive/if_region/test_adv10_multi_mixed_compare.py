import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv10MultiMixedCompare(ExhaustiveTestCase):
    # if 条件多重比较混合运算符 a < b <= c > d >= e
    SOURCE_CODE = """if a < b <= c > d >= e:
    x = 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
