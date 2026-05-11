import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN30IfInForBreak_x_var2(ExhaustiveTestCase):
    SOURCE_CODE = """for x in range(10):
    if x > 5:
        break"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
