import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv08AnnAssignNoValue(ExhaustiveTestCase):
    # if 体内 ann assign 无初始值 x: int
    SOURCE_CODE = """if c:
    x: int"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
