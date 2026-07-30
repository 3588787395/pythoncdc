import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR4WhileTryFinallyReturn(ExhaustiveTestCase):
    SOURCE_CODE = """def f():
    while a:
        try:
            if b:
                return 1
        finally:
            cleanup()"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
