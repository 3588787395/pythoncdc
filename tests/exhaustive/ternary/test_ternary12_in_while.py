import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTernary12InWhile(ExhaustiveTestCase):
    SOURCE_CODE = """while (next_item() if has_more() else None):
    pass"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
