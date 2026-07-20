import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv05LambdaPosonly(ExhaustiveTestCase):
    # if 条件中带 positional-only 参数 lambda
    SOURCE_CODE = """if (lambda x, /: x + 1)(5) > 3:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
