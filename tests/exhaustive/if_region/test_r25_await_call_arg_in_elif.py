import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR25AwaitCallArgInElif(ExhaustiveTestCase):
    SOURCE_CODE = """async def f(x):
    if x > 0:
        return process(await fetch(x), await fetch(x + 1))
    elif x < 0:
        return process(await fetch(-x))
    else:
        return process(0)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
