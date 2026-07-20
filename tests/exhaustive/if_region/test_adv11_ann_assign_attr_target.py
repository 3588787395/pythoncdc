import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11AnnAssignAttrTarget(ExhaustiveTestCase):
    # if 体内属性目标的注解赋值 x.y: int = 1
    SOURCE_CODE = """if c:
    x.y: int = 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
