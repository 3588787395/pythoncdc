import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestBool12InForCond(ExhaustiveTestCase):
    SOURCE_CODE = """for x in items:
    if x is not None and x > 0:
        pass"""
    REGION_TYPE = "BOOL_OP"

    def test_decompile(self):
        self.verify_decompilation()
