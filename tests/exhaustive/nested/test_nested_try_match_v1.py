import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestNestedTryMatch_v1(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    match v:
        case 1: y = 1
        case _: y = 2
except:
    pass"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
