import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF03IfElif_x_0_1(ExhaustiveTestCase):
    SOURCE_CODE = """if x > 0:
    x = 1
elif x > 1:
    x = 2"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
