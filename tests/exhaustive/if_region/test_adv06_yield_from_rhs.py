import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv06YieldFromRhs(ExhaustiveTestCase):
    # if 体内 yield from 作赋值右值
    SOURCE_CODE = """def f():
    if c:
        x = yield from g()
    return x"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
