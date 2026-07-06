import sys
sys.path.insert(0, '/workspace')

from tests.exhaustive.ternary.test_ternary12_in_while import TestTernary12InWhile
TestTernary12InWhile.setUpClass()
t = TestTernary12InWhile()
code = t.compile_source()
from core.cfg import CFGBuilder, RegionASTGenerator
cfg = CFGBuilder().build(code)
gen = RegionASTGenerator(cfg)
ra = gen.region_analyzer

# Check block@44 (the false-value target) in detail
b44 = cfg.get_block_by_offset(44)
print('block@44 ALL instructions:')
for i in b44.instructions:
    print(f'  {i.offset}: {i.opname} {i.argval!r}')

print(f'\\n_is_single_expression_block result: {ra._is_single_expression_block(b44)}')

# Manually trace through _is_single_expression_block logic
NOISE_OPS = frozenset({'RESUME', 'NOP', 'CACHE', 'PUSH_NULL'})
effective = [i for i in b44.instructions if i.opname not in NOISE_OPS]
print(f'After noise filter ({len(effective)}): {[i.opname for i in effective]}')

while effective and effective[-1].opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'):
    effective = effective[:-1]
    print(f'After jump trim ({len(effective)}): {[i.opname for i in effective]}')

FORWARD_CONDITIONAL_JUMP_OPS = frozenset({'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE'})
SHORT_CIRCUIT_JUMP_OPS = frozenset({'JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP'})
if effective and effective[-1].opname in (FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS):
    effective = effective[:-1]
    print(f'After cond jump trim ({len(effective)}): {[i.opname for i in effective]}')

store_or_terminal_ops = frozenset({
    'STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL', 'STORE_ATTR', 'STORE_SUBSCR',
    'DELETE_NAME', 'DELETE_FAST', 'DELETE_GLOBAL', 'DELETE_ATTR',
    'RAISE_VARARGS', 'YIELD_VALUE', 'IMPORT_NAME', 'IMPORT_FROM', 'IMPORT_STAR',
    'GLOBAL', 'NONLOCAL',
})
allowed_terminal_ops = frozenset({'RETURN_VALUE', 'RETURN_CONST'})

for idx, instr in enumerate(effective):
    is_last = idx == len(effective) - 1
    in_store = instr.opname in store_or_terminal_ops
    is_jump = instr.opname.startswith('JUMP_') or instr.opname.startswith('POP_JUMP_')
    early_term = not is_last and instr.opname in allowed_terminal_ops
    print(f'  [{idx}] {instr.opname} last={is_last} store={in_store} jump={is_jump} early_term={early_term}')
    if in_store:
        print('  -> REJECT (store/terminal)')
        break
    if is_jump:
        print('  -> REJECT (jump)')
        break
    if early_term:
        print('  -> REJECT (early terminal)')
        break
