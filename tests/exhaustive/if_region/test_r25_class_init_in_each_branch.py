import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR25ClassInitInEachBranch(ExhaustiveTestCase):
    SOURCE_CODE = """def f(mode):
    if mode == 'a':
        class A:
            def __init__(self, x):
                self.x = x
            def get(self):
                return self.x
        return A(1)
    elif mode == 'b':
        class B:
            def __init__(self, y):
                self.y = y
        return B(2)
    else:
        return None"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
