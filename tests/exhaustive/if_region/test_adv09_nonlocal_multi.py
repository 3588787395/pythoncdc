import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09NonlocalMulti(ExhaustiveTestCase):
    # if 体内 nonlocal 多名声明 nonlocal x, y
    SOURCE_CODE = """def outer():
    x = 0
    y = 0
    def inner():
        if cond:
            nonlocal x, y
            x = 1
            y = 2"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
