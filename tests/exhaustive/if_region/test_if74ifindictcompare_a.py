import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF74Ifindictcompare_a(ExhaustiveTestCase):
    SOURCE_CODE = """d = {1: 2}
if a in d:
    a = d[a]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
