"""Round 01 IF - test 489"""
import sys
sys.path.insert(0, r"F:\Downloads\pythoncdc-main")
from core.cfg import decompile

SOURCE = 'if a and b:\n    r = 1\nelif c or d:\n    r = 2'

def test_489():
    result = decompile(SOURCE)
    assert result is not None, "Decompilation returned None"
    compiled = compile(result, "<test>", "exec")