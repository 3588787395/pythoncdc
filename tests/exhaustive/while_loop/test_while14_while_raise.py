import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestWhile14WhileRaise(ExhaustiveTestCase):
    SOURCE_CODE = """while tasks:
    task = tasks.pop(0)
    if timeout(task):
        raise TimeoutError(f"Task {task.id} timed out")
    execute(task)"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
