import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR25TryElseFinallyInElifBody(ExhaustiveTestCase):
    SOURCE_CODE = """def f(x):
    if x > 0:
        return x
    elif x < 0:
        try:
            r = process(-x)
        except ValueError:
            r = -1
        else:
            r = r + 1
        finally:
            cleanup()
        return r
    else:
        return 0"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
