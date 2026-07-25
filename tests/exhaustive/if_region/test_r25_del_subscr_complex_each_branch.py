import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR25DelSubscrComplexEachBranch(ExhaustiveTestCase):
    SOURCE_CODE = """def f(x, items):
    if x > 0:
        del items[x]
    elif x < 0:
        del items[x:x+10]
        del items[-1]
    else:
        del items[:]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
