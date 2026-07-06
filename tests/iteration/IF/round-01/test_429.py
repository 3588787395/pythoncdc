"""Round 01 IF - test 429"""
import sys
sys.path.insert(0, r"F:\Downloads\pythoncdc-main")
from core.cfg import decompile

SOURCE = 'if a and b:\n    if c:\n        r = 1\n    elif d:\n        r = 2\nelif z:\n    r = 3'

def test_429():
    result = decompile(SOURCE)
    assert result is not None, "Decompilation returned None"
    compiled = compile(result, "<test>", "exec")