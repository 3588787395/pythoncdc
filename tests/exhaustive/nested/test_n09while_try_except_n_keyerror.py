import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN09While_Try_Except_n_KeyError(ExhaustiveTestCase):
    SOURCE_CODE = """def f(d, keys):
    while keys:
        key = keys.pop()
        try:
            n = d[key]
        except KeyError:
            n = None"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
