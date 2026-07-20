import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11ForAttrTarget(ExhaustiveTestCase):
    # if 体内 for 循环变量为属性目标 for x.a in pairs
    SOURCE_CODE = """if c:
    for x.a in pairs:
        pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
