"""Debug: trace parse_comprehension_inner output for get_open_orders"""
import sys, os, types, marshal, dis
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.ast_generator_v2 import ExpressionReconstructor
from core.cfg.comprehension_generator import ComprehensionGenerator

# Load the pyc
pyc_path = "site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc"
with open(pyc_path, 'rb') as f:
    f.read(16)
    orig_code = marshal.load(f)

# Find the TradeLiveBroker class
def find_code(code, name):
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            if c.co_name == name:
                return c
            result = find_code(c, name)
            if result:
                return result
    return None

broker_code = find_code(orig_code, 'TradeLiveBroker')
goo_code = find_code(broker_code, 'get_open_orders')

# Find the listcomp code object
listcomp_code = None
for c in goo_code.co_consts:
    if isinstance(c, types.CodeType) and c.co_name == '<listcomp>':
        listcomp_code = c
        break

print(f"Listcomp code: {listcomp_code.co_name}")
print(f"Listcomp varnames: {listcomp_code.co_varnames}")

# Create expression reconstructor and comprehension generator
expr_recon = ExpressionReconstructor()
comp_gen = ComprehensionGenerator(expr_recon)

# Simulate the iter_instrs: LOAD_FAST self, LOAD_ATTR orders
class FakeInstr:
    def __init__(self, opname, argval, arg=None):
        self.opname = opname
        self.argval = argval
        self.arg = arg
        self.starts_line = 1
        self.offset = 0

iter_instrs = [
    FakeInstr('LOAD_FAST', 'self', arg=0),
    FakeInstr('LOAD_ATTR', 'orders', arg=0),  # arg=0 means is_method_form=False
]

iter_expr = expr_recon.reconstruct(iter_instrs)
print(f"\niter_expr from reconstruct: {iter_expr}")
print(f"  type: {iter_expr.get('type')}")
print(f"  is_method_form: {iter_expr.get('is_method_form', 'NOT SET')}")
print(f"  attr: {iter_expr.get('attr')}")
print(f"  value: {iter_expr.get('value')}")

# Strip is_method_form (as our fix does)
if isinstance(iter_expr, dict) and iter_expr.get('type') == 'Attribute':
    iter_expr.pop('is_method_form', None)
    print(f"  After strip: is_method_form removed")

# Now call parse_comprehension_inner
comp_ast = comp_gen.parse_comprehension_inner(listcomp_code, iter_expr)
print(f"\ncomp_ast: {comp_ast}")
if comp_ast:
    print(f"  type: {comp_ast.get('type')}")
    generators = comp_ast.get('generators', [])
    for g in generators:
        print(f"  generator iter: {g.get('iter')}")
        print(f"  generator iter type: {g.get('iter', {}).get('type')}")
        if g.get('iter', {}).get('type') == 'Call':
            print(f"  *** BUG: iter is Call instead of Attribute! ***")
            print(f"  iter func: {g.get('iter', {}).get('func')}")
        elif g.get('iter', {}).get('type') == 'Attribute':
            print(f"  OK: iter is Attribute (correct)")
