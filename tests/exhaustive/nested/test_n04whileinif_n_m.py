import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN04WhileInIf_n_m(ExhaustiveTestCase):
    SOURCE_CODE = """if n > 0:
    while m > 0:
        m -= 1"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
