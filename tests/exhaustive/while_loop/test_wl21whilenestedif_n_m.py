import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestWL21WhileNestedIf_n_m(ExhaustiveTestCase):
    SOURCE_CODE = """while n > 0:
    if m > 0:
        m -= 1
    n -= 1"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
