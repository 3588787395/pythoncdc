import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR25AwaitInSubscrEachBranch(ExhaustiveTestCase):
    SOURCE_CODE = """async def f(x):
    if x > 0:
        return data[await fetch(x)]
    elif x < 0:
        return (await fetch(-x))[0]
    else:
        return data[await fetch(0):]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
