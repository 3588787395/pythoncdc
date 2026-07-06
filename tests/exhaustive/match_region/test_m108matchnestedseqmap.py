import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestM108MatchNestedSeqMap(ExhaustiveTestCase):
    SOURCE_CODE = """def parse_config(cfg):
    match cfg:
        case ["db", {"host": h, "port": p}] if p > 1024:
            result = f"db://{h}:{p}"
        case ["api", [method, path]] if method in ("GET", "POST"):
            result = f"{method} {path}"
        case _:
            result = "invalid"
    return result
"""
    REGION_TYPE = "MATCH_REGION"

    def test_decompile(self):
        self.verify_decompilation()
