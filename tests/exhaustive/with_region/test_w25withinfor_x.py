import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestW25WithInFor_x(ExhaustiveTestCase):
    SOURCE_CODE = """for i in range(3):
    with open('f') as x:
        pass"""
    REGION_TYPE = "WITH_REGION"

    def test_decompile(self):
        self.verify_decompilation()
