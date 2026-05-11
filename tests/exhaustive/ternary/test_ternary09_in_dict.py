import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTernary09InDict(ExhaustiveTestCase):
    SOURCE_CODE = """result = {k: v if v else 'N/A' for k, v in d.items()}"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
