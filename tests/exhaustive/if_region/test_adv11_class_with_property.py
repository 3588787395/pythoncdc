import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11ClassWithProperty(ExhaustiveTestCase):
    # if 体内 class 含 property
    SOURCE_CODE = """if c:
    class C:
        @property
        def x(self):
            return 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
