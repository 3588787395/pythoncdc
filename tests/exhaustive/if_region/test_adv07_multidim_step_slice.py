import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv07MultidimStepSlice(ExhaustiveTestCase):
    # if 体内多维带 step 切片: x[1:2:3, 4:5:6]
    SOURCE_CODE = """if c:
    r = x[1:2:3, 4:5:6]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
