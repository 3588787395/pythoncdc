import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestBO33AndInWhile_a_b(ExhaustiveTestCase):
    SOURCE_CODE = """while a and b:
    a = 0"""
    REGION_TYPE = "BOOL_OP"

    def test_decompile(self):
        self.verify_decompilation()
