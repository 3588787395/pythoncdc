import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestB19Delete_attr_chain(ExhaustiveTestCase):
    SOURCE_CODE = """a = object()
a.b = 1
del a.b.c"""
    REGION_TYPE = "BASIC"

    def test_decompile(self):
        self.verify_decompilation()
