import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestFL50ForNestedElse_n(ExhaustiveTestCase):
    SOURCE_CODE = """for n in range(10):
    if n > 5:
        x = n
    else:
        y = n"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
