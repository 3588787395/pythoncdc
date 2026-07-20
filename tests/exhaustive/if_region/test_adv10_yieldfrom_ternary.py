import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv10YieldfromTernary(ExhaustiveTestCase):
    # if 体内 yield from 三元表达式 yield from (a if c else b)
    SOURCE_CODE = """def f():
    if c:
        yield from (a if cond else b)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
