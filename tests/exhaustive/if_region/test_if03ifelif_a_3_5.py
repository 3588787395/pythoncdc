import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF03IfElif_a_3_5(ExhaustiveTestCase):
    SOURCE_CODE = """if a > 3:
    a = 1
elif a > 5:
    a = 2"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
