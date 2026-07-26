import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR25AugassignTernaryEachBranch(ExhaustiveTestCase):
    SOURCE_CODE = """def f(x, mode):
    if mode == 'a':
        x += (1 if x > 0 else -1)
    elif mode == 'b':
        x -= (2 if x < 0 else 0)
    else:
        x *= (3 if x == 0 else 1)
    return x"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
