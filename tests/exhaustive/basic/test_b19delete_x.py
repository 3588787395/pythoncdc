import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestB19Delete_x(ExhaustiveTestCase):
    SOURCE_CODE = """x = 1
del x"""
    REGION_TYPE = "BASIC"

    def test_decompile(self):
        self.verify_decompilation()
