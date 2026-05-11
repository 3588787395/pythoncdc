import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF74Ifindictcompare_n(ExhaustiveTestCase):
    SOURCE_CODE = """d = {1: 2}
if n in d:
    n = d[n]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
