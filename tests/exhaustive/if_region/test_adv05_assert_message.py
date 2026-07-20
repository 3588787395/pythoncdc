import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv05AssertMessage(ExhaustiveTestCase):
    # if 体内 assert with message
    SOURCE_CODE = """if c:
    assert x > 0, 'positive'"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
