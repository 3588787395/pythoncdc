import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv06ReversedSlice(ExhaustiveTestCase):
    # if 体内 reversed 切片 x[::-1]
    SOURCE_CODE = """if c:
    z = x[::-1]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
