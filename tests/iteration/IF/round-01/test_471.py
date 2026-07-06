"""Round 01 IF - test 471"""
import sys
sys.path.insert(0, r"F:\Downloads\pythoncdc-main")
from core.cfg import decompile

SOURCE = 'if a:\n    r = 1\nelif b:\n    r = 2\nelif c:\n    r = 3\nelif d:\n    r = 4\nelse:\n    r = 5'

def test_471():
    result = decompile(SOURCE)
    assert result is not None, "Decompilation returned None"
    compiled = compile(result, "<test>", "exec")