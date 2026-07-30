import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR4WhileTryFinallyBreakInFinally(ExhaustiveTestCase):
    SOURCE_CODE = """while a:
    try:
        do()
    finally:
        if b:
            break"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
