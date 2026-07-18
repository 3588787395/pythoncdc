import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv07LambdaVarargs(ExhaustiveTestCase):
    # if 体内 lambda 带 *args 和 **kwargs: lambda *a, **k: a
    SOURCE_CODE = """if c:
    f = lambda *a, **k: a"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
