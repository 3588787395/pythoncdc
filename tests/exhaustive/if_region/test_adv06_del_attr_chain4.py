import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv06DelAttrChain4(ExhaustiveTestCase):
    # if 体内 del 嵌套属性链 del a.b.c.d
    SOURCE_CODE = """if c:
    del a.b.c.d"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
