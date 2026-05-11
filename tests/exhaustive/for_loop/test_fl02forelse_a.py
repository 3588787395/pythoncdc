import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestFL02ForElse_a(ExhaustiveTestCase):
    SOURCE_CODE = """for a in range(10):
    pass
else:
    a = -1"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
