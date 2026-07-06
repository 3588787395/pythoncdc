import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF03IfElif_n_42_100(ExhaustiveTestCase):
    SOURCE_CODE = """if n > 42:
    n = 1
elif n > 100:
    n = 2"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
