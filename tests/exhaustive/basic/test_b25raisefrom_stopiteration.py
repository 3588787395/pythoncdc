import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestB25RaiseFrom_StopIteration(ExhaustiveTestCase):
    SOURCE_CODE = """raise StopIteration from None"""
    REGION_TYPE = "BASIC"

    def test_decompile(self):
        self.verify_decompilation()
