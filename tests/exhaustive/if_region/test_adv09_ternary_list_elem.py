import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09TernaryAsListElem(ExhaustiveTestCase):
    # if 体内三元作 list literal 元素 r = [a if c else b, d if e else f]
    SOURCE_CODE = """if c:
    r = [a if cond else b, d if e else f]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
