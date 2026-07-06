import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF43Ifinwhile_n(ExhaustiveTestCase):
    SOURCE_CODE = """while n > 0:
    if n > 5:
        n = n - 5
    else:
        n = n - 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
