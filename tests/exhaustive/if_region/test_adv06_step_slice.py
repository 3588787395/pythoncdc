import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv06StepSlice(ExhaustiveTestCase):
    # if 体内 step 切片 x[1:10:2]
    SOURCE_CODE = """if c:
    z = x[1:10:2]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
