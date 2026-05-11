import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTE04TernaryFuncParam_n(ExhaustiveTestCase):
    SOURCE_CODE = """def g(name, age):
    return f"{name}: {'adult' if age >= 18 else 'minor'}"
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
