import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN13Try_For_If_Break_n_ValueError(ExhaustiveTestCase):
    SOURCE_CODE = """def f(values):
    try:
        for v in values:
            if isinstance(v, str) and not v.isdigit():
                break
            n = v
    except ValueError:
        n = 0"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
