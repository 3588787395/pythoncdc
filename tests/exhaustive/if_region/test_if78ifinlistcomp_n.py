import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF78Ifinlistcomp_n(ExhaustiveTestCase):
    SOURCE_CODE = """r = [i for i in range(10) if n > i]"""
    REGION_TYPE = "BASIC"

    def test_decompile(self):
        self.verify_decompilation()
