import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestW19WithBreak_x(ExhaustiveTestCase):
    SOURCE_CODE = """for x in range(10):
    with open('f') as f:
        break"""
    REGION_TYPE = "WITH_REGION"

    def test_decompile(self):
        self.verify_decompilation()
