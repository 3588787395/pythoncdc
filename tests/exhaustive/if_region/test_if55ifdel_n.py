import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF55Ifdel_n(ExhaustiveTestCase):
    SOURCE_CODE = """d = {"n": 1}
if n > 0:
    del d["n"]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
