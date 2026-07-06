import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestB03AugAssignSub_a_3(ExhaustiveTestCase):
    SOURCE_CODE = """a -= 3"""
    REGION_TYPE = "BASIC"

    def test_decompile(self):
        self.verify_decompilation()
