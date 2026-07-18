import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv04YieldRhsAssign(ExhaustiveTestCase):
    # yield 作赋值右值（x = yield g()）
    SOURCE_CODE = """def f():
    if c:
        x = yield g()
    return x"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
