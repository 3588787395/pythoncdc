import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN21IfInWhileBody_x_y(ExhaustiveTestCase):
    SOURCE_CODE = """while x > 0:
    if x > 2:
        y = x
    x -= 1"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
