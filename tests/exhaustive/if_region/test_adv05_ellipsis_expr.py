import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv05EllipsisExpr(ExhaustiveTestCase):
    # if 体内 Ellipsis 作表达式 a = ...
    SOURCE_CODE = """if c:
    x = ..."""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
