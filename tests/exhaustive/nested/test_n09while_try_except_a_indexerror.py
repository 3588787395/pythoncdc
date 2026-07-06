import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN09While_Try_Except_a_IndexError(ExhaustiveTestCase):
    SOURCE_CODE = """def f(data):
    while len(data) > 0:
        try:
            a = data.pop()
        except IndexError:
            a = None
            break"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
