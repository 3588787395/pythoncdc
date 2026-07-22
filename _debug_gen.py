import sys
sys.path.insert(0, '/workspace')
from tests.control_flow_matrix.base import ControlFlowTestCase

class T(ControlFlowTestCase):
    SOURCE_CODE = ""

cases = {
    'r14_compare': "while (a if c else b) > 0:\n    pass\n",
    'r14_walrus': "while (n := (a if c else b)) > 0:\n    pass\n",
    'r3_simple': "while (a if cond else b):\n    pass\n",
}
for name, src in cases.items():
    T.SOURCE_CODE = src
    T.setUpClass()
    t = T()
    try:
        out = t.decompile()
        print(f"=== {name} ===\n{out!r}\n")
    except Exception as e:
        print(f"=== {name} === ERROR: {e}\n")
