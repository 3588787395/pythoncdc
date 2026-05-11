import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTernary19StringExpr(ExhaustiveTestCase):
    SOURCE_CODE = """msg = f"Got {n} item{'s' if n != 1 else ''}\""""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
