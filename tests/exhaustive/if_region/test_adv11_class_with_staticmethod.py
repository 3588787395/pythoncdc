import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11ClassWithStaticmethod(ExhaustiveTestCase):
    # if 体内 class 含 staticmethod
    SOURCE_CODE = """if c:
    class C:
        @staticmethod
        def f():
            return 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
