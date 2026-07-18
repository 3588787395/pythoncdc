import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09TernaryAsDictKeyAndValue(ExhaustiveTestCase):
    # if 体内字典字面量 key 和 value 同时含三元 d[k if c else m] = v
    SOURCE_CODE = """if c:
    d[k if cond else m] = v"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
