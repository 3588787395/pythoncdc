import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestNestedWhileBoolop_v3(ExhaustiveTestCase):
    SOURCE_CODE = """while p:
    q = p and q and r"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
