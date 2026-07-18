import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv06TryFinallyNested(ExhaustiveTestCase):
    # if 体内 try-finally 嵌套 try-except
    SOURCE_CODE = """if c:
    try:
        try:
            x = 1
        except E:
            x = 2
    finally:
        cleanup()"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
