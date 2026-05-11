import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF43Ifinwhile_x(ExhaustiveTestCase):
    SOURCE_CODE = """while x > 0:
    if x > 5:
        x = x - 5
    else:
        x = x - 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
