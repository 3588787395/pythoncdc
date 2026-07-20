import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv03NestedTernaryChain(ExhaustiveTestCase):
    SOURCE_CODE = """if 0 < (a if (b if c else d) else e) < 10:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
