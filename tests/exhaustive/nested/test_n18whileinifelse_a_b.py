import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN18WhileInIfElse_a_b(ExhaustiveTestCase):
    SOURCE_CODE = """if a > 0:
    while b > 0:
        b -= 1
else:
    a = 0"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
