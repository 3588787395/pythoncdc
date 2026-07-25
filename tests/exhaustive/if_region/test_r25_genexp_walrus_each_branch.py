import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR25GenexpWalrusEachBranch(ExhaustiveTestCase):
    SOURCE_CODE = """def f(items, mode):
    if mode == 'a':
        return sum((n := x) for x in items if n > 0)
    elif mode == 'b':
        return list((n := x) * 2 for x in items)
    else:
        return max((n := x) for x in items)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
