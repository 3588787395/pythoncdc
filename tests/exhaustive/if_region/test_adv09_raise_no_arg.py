import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09RaiseNoArg(ExhaustiveTestCase):
    # if 体内 raise 无参数（re-raise，需 except 上下文）
    SOURCE_CODE = """def f():
    try:
        do_stuff()
    except Exception:
        if c:
            raise"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
