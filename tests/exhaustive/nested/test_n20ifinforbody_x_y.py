import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN20IfInForBody_x_y(ExhaustiveTestCase):
    SOURCE_CODE = """for x in range(5):
    if x > 2:
        y = x"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
