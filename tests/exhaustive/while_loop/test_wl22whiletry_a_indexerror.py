import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestWL22WhileTry_a_IndexError(ExhaustiveTestCase):
    SOURCE_CODE = """while a > 0:
    try:
        a -= 1
    except IndexError:
        a = 0"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
