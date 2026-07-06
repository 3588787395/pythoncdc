import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN08For_Try_Except_a_IndexError(ExhaustiveTestCase):
    SOURCE_CODE = """def f(items):
    for item in items:
        try:
            a = item[0]
        except IndexError:
            a = None"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
