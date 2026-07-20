import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11ForSubscrTarget(ExhaustiveTestCase):
    # if 体内 for 循环变量为下标目标 for x[0] in pairs
    SOURCE_CODE = """if c:
    for x[0] in pairs:
        pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
