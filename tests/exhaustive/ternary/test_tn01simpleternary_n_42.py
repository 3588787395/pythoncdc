import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTN01SimpleTernary_n_42(ExhaustiveTestCase):
    SOURCE_CODE = """n if n > 0 else 42"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
