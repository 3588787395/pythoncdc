"""Round 01 IF - test 476"""
import sys
sys.path.insert(0, r"F:\Downloads\pythoncdc-main")
from core.cfg import decompile

SOURCE = 'while x or a:\n    if x or b:\n        r = 1\n    elif c:\n        r = 2'

def test_476():
    result = decompile(SOURCE)
    assert result is not None, "Decompilation returned None"
    compiled = compile(result, "<test>", "exec")