import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF89Ifnestedwith_n(ExhaustiveTestCase):
    SOURCE_CODE = """if n > 0:
    with open("f") as f:
        n = f.read()"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
