import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv10TernaryInSetLiteral(ExhaustiveTestCase):
    # if 体内三元在集合字面量元素 {a if c else b}
    SOURCE_CODE = """if c:
    x = {a if cond else b}"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
