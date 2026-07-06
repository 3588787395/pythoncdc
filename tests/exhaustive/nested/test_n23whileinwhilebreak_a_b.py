import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN23WhileInWhileBreak_a_b(ExhaustiveTestCase):
    SOURCE_CODE = """while a > 0:
    while b > 0:
        b -= 1
        if b == 0:
            break
    a -= 1"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
