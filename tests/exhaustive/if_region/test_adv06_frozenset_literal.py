import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv06FrozensetLiteral(ExhaustiveTestCase):
    # if 体内 frozenset/set 字面量赋值 r = {1, 2, 3}
    SOURCE_CODE = """if c:
    r = {1, 2, 3}"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
