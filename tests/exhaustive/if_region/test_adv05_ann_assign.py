import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv05AnnAssign(ExhaustiveTestCase):
    # if 体内带注解的赋值 x: int = 1
    SOURCE_CODE = """if c:
    x: int = 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
