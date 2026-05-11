import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN32TryInForBreak_x_ValueError(ExhaustiveTestCase):
    SOURCE_CODE = """for x in range(10):
    try:
        if x == 5:
            break
    except ValueError:
        continue"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
