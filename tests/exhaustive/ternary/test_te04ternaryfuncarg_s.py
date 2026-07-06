import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTE04TernaryAsFuncArg_n(ExhaustiveTestCase):
    SOURCE_CODE = """print(s if s else "default")"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
