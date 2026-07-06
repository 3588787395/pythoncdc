"""Round 01 IF - test 488"""
import sys
sys.path.insert(0, r"F:\Downloads\pythoncdc-main")
from core.cfg import decompile

SOURCE = 'while a or a:\n    if a or b:\n        r = 1\n    elif c:\n        r = 2'

def test_488():
    result = decompile(SOURCE)
    assert result is not None, "Decompilation returned None"
    compiled = compile(result, "<test>", "exec")