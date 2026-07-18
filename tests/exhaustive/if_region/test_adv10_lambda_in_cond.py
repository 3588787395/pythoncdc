import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv10LambdaInCond(ExhaustiveTestCase):
    # if 条件中调用 lambda if (lambda x: x > 0)(val):
    SOURCE_CODE = """if (lambda x: x > 0)(val):
    y = 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
