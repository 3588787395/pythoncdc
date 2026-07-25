import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR25TryFinallyRaiseEachBranch(ExhaustiveTestCase):
    SOURCE_CODE = """def f(x):
    if x > 0:
        try:
            r = process(x)
        finally:
            cleanup()
        return r
    elif x < 0:
        try:
            r = process(-x)
        finally:
            cleanup()
        return r
    else:
        raise ValueError('zero')"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
