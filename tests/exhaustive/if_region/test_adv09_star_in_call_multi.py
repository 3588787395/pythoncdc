import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09StarInCallMulti(ExhaustiveTestCase):
    # if 体内调用中多星号解包 f(*a, *b)
    SOURCE_CODE = """if c:
    f(*a, *b)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
