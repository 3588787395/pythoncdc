import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestBool16NestedBoolop(ExhaustiveTestCase):
    SOURCE_CODE = """if (a or b) and (c or d) and (e or f):
    pass"""
    REGION_TYPE = "BOOL_OP"

    def test_decompile(self):
        self.verify_decompilation()
