import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTernary15InTry(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    val = expr if cond else alt
except:
    val = None"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
