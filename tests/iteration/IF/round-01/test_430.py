"""Round 01 IF - test 430"""
import sys
sys.path.insert(0, r"F:\Downloads\pythoncdc-main")
from core.cfg import decompile

SOURCE = 'if a or b:\n    if c:\n        r = 1\n    else:\n        r = 2\nelif z:\n    r = 3'

def test_430():
    result = decompile(SOURCE)
    assert result is not None, "Decompilation returned None"
    compiled = compile(result, "<test>", "exec")