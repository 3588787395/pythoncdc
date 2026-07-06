import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF87Ifnestedwhile_n(ExhaustiveTestCase):
    SOURCE_CODE = """if n > 0:
    while n > 10:
        n = n - 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
