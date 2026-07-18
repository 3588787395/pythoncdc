import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09TernarySubscrRhs(ExhaustiveTestCase):
    # if 体内三元作下标 a[b if c else d] 取值
    SOURCE_CODE = """if c:
    r = a[b if cond else d]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
