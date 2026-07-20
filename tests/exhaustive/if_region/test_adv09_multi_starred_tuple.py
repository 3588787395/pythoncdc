import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09MultiStarredTuple(ExhaustiveTestCase):
    # if 体内多元组带多个星号 r = (a, *b, *c, d)
    SOURCE_CODE = """if c:
    r = (a, *b, *c, d)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
