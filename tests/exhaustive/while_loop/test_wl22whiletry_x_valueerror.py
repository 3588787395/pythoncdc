import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestWL22WhileTry_x_ValueError(ExhaustiveTestCase):
    SOURCE_CODE = """while x > 0:
    try:
        x -= 1
    except ValueError:
        x = 0"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
