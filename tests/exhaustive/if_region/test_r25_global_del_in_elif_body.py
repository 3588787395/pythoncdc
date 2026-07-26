import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR25GlobalDelInElifBody(ExhaustiveTestCase):
    SOURCE_CODE = """g = 0
def f(mode):
    global g
    if mode == 'a':
        g = 1
        del g
        g = 10
    elif mode == 'b':
        g = 2
    else:
        return g"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
