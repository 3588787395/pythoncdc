import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09TernaryInTupleArg(ExhaustiveTestCase):
    # if 体内调用中元组参数含三元 f((a if c else b))
    SOURCE_CODE = """if c:
    f(a if cond else b)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
