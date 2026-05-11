import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN13TryInWhile_n_StopIteration(ExhaustiveTestCase):
    SOURCE_CODE = """while n > 0:
    try:
        n -= 1
    except StopIteration:
        n = 0"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
