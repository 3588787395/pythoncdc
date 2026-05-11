import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTernary06InReturn(ExhaustiveTestCase):
    SOURCE_CODE = """return success_val if ok else error_val"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
