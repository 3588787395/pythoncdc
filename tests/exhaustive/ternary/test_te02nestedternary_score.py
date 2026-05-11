import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTE02NestedTernary_n(ExhaustiveTestCase):
    SOURCE_CODE = '''grade = "A" if score >= 90 else ("B" if score >= 80 else ("C" if score >= 70 else "F"))'''
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
