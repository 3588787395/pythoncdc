import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv08StarredInListLiteral(ExhaustiveTestCase):
    # if 体内 list 字面量带星号解包 [*a, *b, c]
    SOURCE_CODE = """if c:
    r = [*a, *b, c]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
