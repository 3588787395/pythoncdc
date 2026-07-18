import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv05Chaincmp5Levels(ExhaustiveTestCase):
    # if 体内 chained comparison 多层嵌套 0 < a < b < c < d
    SOURCE_CODE = """if c:
    z = 0 < a < b < c < d"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
