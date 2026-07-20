import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv07LambdaWalrusBody(ExhaustiveTestCase):
    # if 体内 lambda body 含 walrus: lambda x: (n := x + 1)
    SOURCE_CODE = """if c:
    f = lambda x: (n := x + 1)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
