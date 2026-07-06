import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestBO03Not_x(ExhaustiveTestCase):
    SOURCE_CODE = """not x"""
    REGION_TYPE = "BASIC"

    def test_decompile(self):
        self.verify_decompilation()
