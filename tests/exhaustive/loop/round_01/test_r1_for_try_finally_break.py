import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR1ForTryFinallyBreak(ExhaustiveTestCase):
    SOURCE_CODE = """for i in r:
    try:
        if i:
            break
    finally:
        cleanup()"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
