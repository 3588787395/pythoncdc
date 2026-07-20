import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv05TryFinallyNoExcept(ExhaustiveTestCase):
    # if 体内 try-finally 无 except
    SOURCE_CODE = """if c:
    try:
        x = 1
    finally:
        y = 2"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
