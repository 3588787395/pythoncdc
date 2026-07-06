import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestB30SubscriptAssign_n_42(ExhaustiveTestCase):
    SOURCE_CODE = """n[0] = 42"""
    REGION_TYPE = "BASIC"

    def test_decompile(self):
        self.verify_decompilation()
