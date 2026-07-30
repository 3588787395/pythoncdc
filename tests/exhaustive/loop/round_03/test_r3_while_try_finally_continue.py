import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR3WhileTryFinallyContinue(ExhaustiveTestCase):
    SOURCE_CODE = """while a:
    try:
        do()
    finally:
        if b:
            continue"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
