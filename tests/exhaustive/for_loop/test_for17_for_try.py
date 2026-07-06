import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestFor17ForTry(ExhaustiveTestCase):
    SOURCE_CODE = """for item in data:
    try:
        process(item)
    except ValueError:
        skip(item)"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
