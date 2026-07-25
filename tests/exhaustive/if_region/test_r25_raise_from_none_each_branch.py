import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR25RaiseFromNoneEachBranch(ExhaustiveTestCase):
    SOURCE_CODE = """def f(x):
    if x > 0:
        try:
            return process(x)
        except Exception:
            raise ValueError('pos failed') from None
    elif x < 0:
        try:
            return process(-x)
        except Exception:
            raise ValueError('neg failed') from None
    else:
        return 0"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
