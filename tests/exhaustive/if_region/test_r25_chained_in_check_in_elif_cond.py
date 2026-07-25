import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR25ChainedInCheckInElifCond(ExhaustiveTestCase):
    SOURCE_CODE = """def f(a, b, c, d, e, g):
    if a in b:
        return 1
    elif c in d:
        return 2
    else:
        return 3"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
