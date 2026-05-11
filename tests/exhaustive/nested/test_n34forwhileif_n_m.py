import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN34ForWhileIf_n_m(ExhaustiveTestCase):
    SOURCE_CODE = """for n in range(5):
    while m > 0:
        if m > 2:
            m -= 1
        else:
            break"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
