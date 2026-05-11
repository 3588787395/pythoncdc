import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF83Ifelsedel_n(ExhaustiveTestCase):
    SOURCE_CODE = """d = {"k": 1}
if n > 0:
    d["k"] = n
else:
    del d["k"]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
