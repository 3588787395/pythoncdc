import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestB28MultiAssign_a_b_3(ExhaustiveTestCase):
    SOURCE_CODE = """a = b = 3"""
    REGION_TYPE = "BASIC"

    def test_decompile(self):
        self.verify_decompilation()
