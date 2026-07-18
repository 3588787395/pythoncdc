import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11TernarySubscrInCond(ExhaustiveTestCase):
    # if 条件中下标表达式内嵌三元 if x[a if b else c]:
    SOURCE_CODE = """if x[a if b else c]:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
