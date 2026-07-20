import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv04CompoundAugassign(ExhaustiveTestCase):
    # 复合赋值复合目标链（d[k1][k2] += 1）
    SOURCE_CODE = """if c:
    d[k1][k2] += 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
