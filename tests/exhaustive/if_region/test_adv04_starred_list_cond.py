import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv04StarredListCond(ExhaustiveTestCase):
    # if 条件中带星号解包列表字面量（[a, *b, c]）
    SOURCE_CODE = """if [a, *b, c]:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
