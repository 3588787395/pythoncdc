import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF85Ifelseyield_n(ExhaustiveTestCase):
    SOURCE_CODE = """def f(n):
    if n > 0:
        yield n
    else:
        yield 0"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
