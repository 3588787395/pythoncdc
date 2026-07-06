"""Round 01 IF - test 424"""
import sys
sys.path.insert(0, r"F:\Downloads\pythoncdc-main")
from core.cfg import decompile

SOURCE = 'if a and b:\n    r = 1\nelif z:\n    r = 2\nelif w:\n    r = 3\nelse:\n    r = 4'

def test_424():
    result = decompile(SOURCE)
    assert result is not None, "Decompilation returned None"
    compiled = compile(result, "<test>", "exec")