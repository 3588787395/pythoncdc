import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09ChainAssignSubscr(ExhaustiveTestCase):
    # if 体内链式赋值含下标目标 a = b[k] = c
    SOURCE_CODE = """if c:
    a = b[k] = c"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
