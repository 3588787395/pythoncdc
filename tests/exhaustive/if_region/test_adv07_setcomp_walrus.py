import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv07SetcompWalrus(ExhaustiveTestCase):
    # if 体内 setcomp 带 walrus: {(n := f(x)) for x in y}
    SOURCE_CODE = """if c:
    r = {(n := f(x)) for x in y}"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
