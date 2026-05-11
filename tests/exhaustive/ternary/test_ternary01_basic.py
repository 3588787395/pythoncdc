import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTernary01Basic(ExhaustiveTestCase):
    SOURCE_CODE = """x = a if cond else b"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
