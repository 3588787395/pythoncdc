import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv05DictcompWalrus(ExhaustiveTestCase):
    # if 体内 dictcomp + walrus
    SOURCE_CODE = """if c:
    r = {k: (v := f(k)) for k in s}"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
