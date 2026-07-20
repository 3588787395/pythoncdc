import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09WithAsTuple(ExhaustiveTestCase):
    # if 体内 with as 多目标 with ctx as (a, b)
    SOURCE_CODE = """if c:
    with ctx as (a, b):
        print(a, b)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
