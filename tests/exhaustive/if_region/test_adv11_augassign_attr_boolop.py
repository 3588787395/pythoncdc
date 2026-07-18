import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11AugassignAttrBoolop(ExhaustiveTestCase):
    # if 体内属性目标 augmented assign 右侧为 boolop x.y += a and b
    SOURCE_CODE = """if c:
    x.y += a and b"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
