import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIf19ComplexExpr(ExhaustiveTestCase):
    SOURCE_CODE = """if len(items) > 0 and items[0] is not None:
    first = items[0]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
