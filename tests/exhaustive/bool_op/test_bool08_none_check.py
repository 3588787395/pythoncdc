import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestBool08NoneCheck(ExhaustiveTestCase):
    SOURCE_CODE = """if obj is not None and obj.valid():
    use(obj)"""
    REGION_TYPE = "BOOL_OP"

    def test_decompile(self):
        self.verify_decompilation()
