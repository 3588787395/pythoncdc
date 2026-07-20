import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11StarredSetInCond(ExhaustiveTestCase):
    # if 条件中含 starred 集合字面量 in 检查 if c in {*a, *b}:
    SOURCE_CODE = """if c in {*a, *b}:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
