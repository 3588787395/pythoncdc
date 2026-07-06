import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF55Ifdel_a(ExhaustiveTestCase):
    SOURCE_CODE = """d = {"a": 1}
if a > 0:
    del d["a"]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
