import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11AugassignSubscrTernary(ExhaustiveTestCase):
    # if 体内下标目标 augmented assign 右侧为三元 x[0] += a if b else c
    SOURCE_CODE = """if c:
    x[0] += a if b else c"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
