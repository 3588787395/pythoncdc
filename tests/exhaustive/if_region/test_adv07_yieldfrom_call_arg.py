import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv07YieldFromCallArg(ExhaustiveTestCase):
    # if 体内 yield from 作函数调用参数: g(yield from h())
    SOURCE_CODE = """def f():
    if c:
        r = g((yield from h()))
    return r"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
