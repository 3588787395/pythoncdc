import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestFor19ForRaise(ExhaustiveTestCase):
    SOURCE_CODE = """for item in items:
    if not valid(item):
        raise ValueError(f"Invalid: {item}")"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
