import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN23WhileInWhileBreak_x_y(ExhaustiveTestCase):
    SOURCE_CODE = """while x > 0:
    while y > 0:
        y -= 1
        if y == 0:
            break
    x -= 1"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
