import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR25YieldFromEachBranch(ExhaustiveTestCase):
    SOURCE_CODE = """def gen(x, items):
    if x > 0:
        yield from (i for i in items if i > 0)
    elif x < 0:
        yield from (i * 2 for i in items if i < 0)
    else:
        yield from range(10)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
