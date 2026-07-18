import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11ForStarredTarget(ExhaustiveTestCase):
    # if 体内 for 循环变量带 starred 目标
    SOURCE_CODE = """if c:
    for *a, b in pairs:
        pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
