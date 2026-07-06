import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTN01SimpleTernary_a_3(ExhaustiveTestCase):
    SOURCE_CODE = """a if a > 0 else 3"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
