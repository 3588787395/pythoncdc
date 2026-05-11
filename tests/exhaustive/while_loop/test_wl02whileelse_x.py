import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestWL02WhileElse_x(ExhaustiveTestCase):
    SOURCE_CODE = """while x > 0:
    x -= 1
else:
    x = 0"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
