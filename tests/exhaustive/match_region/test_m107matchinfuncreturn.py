import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestM107MatchInFuncReturn(ExhaustiveTestCase):
    SOURCE_CODE = """def classify(data):
    match data:
        case {"type": "user", "name": name} if len(name) > 0:
            return ("valid_user", name)
        case {"type": "admin", "level": lvl} if lvl >= 5:
            return ("super_admin", lvl)
        case [x, y] if x == y:
            return ("pair", x)
        case _:
            return ("unknown", None)
"""
    REGION_TYPE = "MATCH_REGION"

    def test_decompile(self):
        self.verify_decompilation()
