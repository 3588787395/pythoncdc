import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTry12TryFor(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    for item in items:
        process(item)
except ProcessingError:
    recover()"""
    REGION_TYPE = "TRY_EXCEPT"

    def test_decompile(self):
        self.verify_decompilation()
