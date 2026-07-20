import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv08LambdaWithWalrusDefault(ExhaustiveTestCase):
    # if 体内 lambda 默认参数带 walrus lambda x=(n := 1): x
    SOURCE_CODE = """if c:
    f = lambda x=(n := 1): x"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
