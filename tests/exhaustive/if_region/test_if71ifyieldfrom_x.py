import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF71Ifyieldfrom_x(ExhaustiveTestCase):
    SOURCE_CODE = """def f(x):
    if x > 0:
        yield from range(x)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
