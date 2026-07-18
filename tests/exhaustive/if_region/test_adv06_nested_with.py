import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv06NestedWith(ExhaustiveTestCase):
    # if 体内 nested with 嵌套
    SOURCE_CODE = """if c:
    with a as x:
        with b as y:
            z = x + y"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
