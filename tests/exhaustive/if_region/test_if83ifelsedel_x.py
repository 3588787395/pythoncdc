import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF83Ifelsedel_x(ExhaustiveTestCase):
    SOURCE_CODE = """d = {"k": 1}
if x > 0:
    d["k"] = x
else:
    del d["k"]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
