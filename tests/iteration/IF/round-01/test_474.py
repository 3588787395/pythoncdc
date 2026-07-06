"""Round 01 IF - test 474"""
import sys
sys.path.insert(0, r"F:\Downloads\pythoncdc-main")
from core.cfg import decompile

SOURCE = 'while x and a:\n    if x and b:\n        r = 1\n    elif c:\n        r = 2'

def test_474():
    result = decompile(SOURCE)
    assert result is not None, "Decompilation returned None"
    compiled = compile(result, "<test>", "exec")