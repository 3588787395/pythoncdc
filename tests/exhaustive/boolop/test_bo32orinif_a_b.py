import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestBO32OrInIf_a_b(ExhaustiveTestCase):
    SOURCE_CODE = """if a or b:
    a = 0"""
    REGION_TYPE = "BOOL_OP"

    def test_decompile(self):
        self.verify_decompilation()
