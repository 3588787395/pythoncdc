import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN09WhileInWhile_x_y(ExhaustiveTestCase):
    SOURCE_CODE = """while x > 0:
    y = 5
    while y > 0:
        y -= 1
    x -= 1"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
