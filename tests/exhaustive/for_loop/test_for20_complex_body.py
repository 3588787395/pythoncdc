import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestFor20ComplexBody(ExhaustiveTestCase):
    SOURCE_CODE = """results = {}
limit = 10
for i, row in enumerate(data):
    if not row:
        continue
    key = row[0]
    value = process(row[1:])
    results[key] = value
    if len(results) >= limit:
        break"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
