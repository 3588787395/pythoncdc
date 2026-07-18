import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv06TernaryLambdaBody(ExhaustiveTestCase):
    # if 体内 lambda body 为三元
    SOURCE_CODE = """if c:
    f = lambda x: a if x > 0 else b"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
