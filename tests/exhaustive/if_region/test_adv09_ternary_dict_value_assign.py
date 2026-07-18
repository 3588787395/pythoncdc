import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09TernaryDictValueAssign(ExhaustiveTestCase):
    # if 体内字典字面量 value 含三元作赋值右值 d[k] = (v if c else w)
    SOURCE_CODE = """if c:
    d[k] = v if cond else w"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
