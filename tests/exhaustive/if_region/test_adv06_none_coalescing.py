import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv06NoneCoalescing(ExhaustiveTestCase):
    # if 体内 None coalescing 风格三元 x if x is not None else y
    SOURCE_CODE = """if c:
    z = x if x is not None else y"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
