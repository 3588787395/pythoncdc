import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR25YieldEachBranchGenexp(ExhaustiveTestCase):
    SOURCE_CODE = """def gen(x, items):
    if x > 0:
        yield x
        yield from items
    elif x < 0:
        yield from (i * 2 for i in items)
    else:
        yield from range(10)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
