import sys
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator
import marshal

path = '.trae/specs/decompiler-test-comprehensive-10rounds/rounds/round_02/test_engineer/minimal_repros/repro_r2_10_try_wrap_for_else_break.pyc'
with open(path, 'rb') as f:
    f.read(4); f.read(4); f.read(8)
    code = marshal.load(f)

func_code = code.co_consts[1]
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(func_code)

region_analyzer = RegionAnalyzer(cfg)
regions = region_analyzer.analyze()

ast_gen = RegionASTGenerator(cfg, region_analyzer, regions)

block16 = cfg.blocks[16]

# Manually trace the processing
handler_instrs = [i for i in block16.instructions
                  if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL',
                                       'PUSH_EXC_INFO', 'POP_EXCEPT', 'POP_TOP',
                                       'CHECK_EXC_MATCH', 'CHECK_EG_MATCH',
                                       'WITH_EXCEPT_START', 'EXTENDED_ARG')]

print(f"handler_instrs: {[(i.opname, i.arg) for i in handler_instrs]}")

# Simulate the loop
stmts = []
stmt_instrs = []
skip_initial_pop = False
for instr in handler_instrs:
    print(f"\n  Processing: {instr.opname} {instr.arg}")
    print(f"    stmt_instrs before: {[(i.opname, i.arg) for i in stmt_instrs]}")
    
    # Check STORE_FAST handling
    if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF') and stmt_instrs:
        print(f"    STORE_FAST with stmt_instrs - checking...")
        # This path might split stmt_instrs
        has_copy = any(i.opname == 'COPY' and i.arg == 1 for i in stmt_instrs)
        if not has_copy:
            # Check if this is as-var cleanup
            prev_instr = stmt_instrs[-1] if stmt_instrs else None
            if prev_instr and prev_instr.opname == 'LOAD_CONST' and prev_instr.argval is None:
                print(f"    Detected as-var cleanup pattern (LOAD_CONST None + STORE_FAST)")
                # This should be as-var cleanup, not a user assignment
                stmt_instrs.append(instr)
                continue
            # Build statement from stmt_instrs
            print(f"    Building statement from stmt_instrs: {[(i.opname, i.arg) for i in stmt_instrs]}")
            stmt = ast_gen._build_statement(stmt_instrs)
            if stmt:
                print(f"    Built statement: {stmt}")
                stmts.append(stmt)
            stmt_instrs = [instr]
            continue
    
    if instr.opname in ('DELETE_FAST', 'DELETE_NAME', 'DELETE_GLOBAL', 'DELETE_DEREF'):
        print(f"    DELETE_FAST - adding to stmt_instrs")
        stmt_instrs.append(instr)
        continue
    
    if instr.opname in ('RETURN_VALUE', 'RETURN_CONST'):
        print(f"    RETURN_VALUE - stmt_instrs: {[(i.opname, i.arg) for i in stmt_instrs]}")
        # Filter POP_TOP
        _filtered = [i for i in stmt_instrs if i.opname != 'POP_TOP']
        print(f"    _filtered: {[(i.opname, i.arg) for i in _filtered]}")
        # Check if only LOAD_CONST None
        is_only_load_none = (len(_filtered) == 1 and _filtered[0].opname == 'LOAD_CONST' and _filtered[0].argval is None)
        print(f"    is_only_load_none: {is_only_load_none}")
        
        if not is_only_load_none and _filtered:
            # Reconstruct return value
            value_instrs = list(_filtered)
            expr = ast_gen.expr_reconstructor.reconstruct(value_instrs) if value_instrs else None
            print(f"    Reconstructed expr: {expr}")
            if expr:
                stmts.append({'type': 'Return', 'value': expr})
                stmt_instrs = []
                continue
        stmt_instrs = []
        continue
    
    stmt_instrs.append(instr)
    print(f"    stmt_instrs after: {[(i.opname, i.arg) for i in stmt_instrs]}")

print(f"\nFinal stmts: {stmts}")
