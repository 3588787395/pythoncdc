import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv06LambdaKwDefault(ExhaustiveTestCase):
    # if 体内 lambda 带 kw-only default and annotations
    SOURCE_CODE = """if c:
    f = lambda x, *, y=10: x + y"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
