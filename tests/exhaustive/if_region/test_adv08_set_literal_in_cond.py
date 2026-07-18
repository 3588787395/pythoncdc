import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv08SetLiteralInCond(ExhaustiveTestCase):
    # if 条件含 set 字面量 in 检查 if x in {1, 2, 3}:
    SOURCE_CODE = """if x in {1, 2, 3}:
    r = 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
