import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR25NonlocalNestedFuncEachBranch(ExhaustiveTestCase):
    SOURCE_CODE = """def f(x):
    counter = 0
    if x > 0:
        def inc():
            nonlocal counter
            counter += 1
            return counter
        return inc()
    elif x < 0:
        def dec():
            nonlocal counter
            counter -= 1
            return counter
        return dec()
    else:
        return counter"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
