import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN22ForInForBreak_x_y(ExhaustiveTestCase):
    SOURCE_CODE = """for x in range(3):
    for y in range(3):
        if y == 1:
            break"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
