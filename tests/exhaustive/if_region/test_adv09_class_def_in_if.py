import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09ClassDefInIf(ExhaustiveTestCase):
    # if 体内 class 定义
    SOURCE_CODE = """if c:
    class C:
        def m(self):
            return 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
