import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestE04TryFinally_a(ExhaustiveTestCase):
    SOURCE_CODE = """def f(a):
    try:
        a[0]
    finally:
        a = []"""
    REGION_TYPE = "TRY_EXCEPT"

    def test_decompile(self):
        self.verify_decompilation()
