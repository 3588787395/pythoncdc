import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv07ChaincmpInList(ExhaustiveTestCase):
    # if 体内链式 in 比较 with list 中段: x in [a, b] in c
    SOURCE_CODE = """if c:
    z = x in [a, b] in cc"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
