import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestFL17ForNestedIf_n_m(ExhaustiveTestCase):
    SOURCE_CODE = """for n in range(5):
    if n > 2:
        m = n"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
