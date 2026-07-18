import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv06MultitargetAnnAssign(ExhaustiveTestCase):
    # if 体内 ann-assign 带嵌套类型注解
    SOURCE_CODE = """if c:
    x: list = [1, 2, 3]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
