import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestW17WithReturn_x(ExhaustiveTestCase):
    SOURCE_CODE = """def f():
    with open('f') as x:
        return x"""
    REGION_TYPE = "WITH_REGION"

    def test_decompile(self):
        self.verify_decompilation()
