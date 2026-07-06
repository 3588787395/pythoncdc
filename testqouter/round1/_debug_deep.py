# Deep debug: trace loop detection for test_l04 and test_l05
import sys, os, py_compile, dis, marshal, types, struct

sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')

test_dir = r'd:\Desktop\ptrade相关\pythoncdc\testqouter\round1'

def debug_test(name):
    print(f"\n{'='*60}")
    print(f"=== {name} ===")
    print(f"{'='*60}")
    
    py_path = os.path.join(test_dir, name + '.py')
    pyc_path = py_path + 'c'
    py_compile.compile(py_path, pyc_path, doraise=True)
    
    with open(pyc_path, 'rb') as f:
        f.read(16)  # header
        code = marshal.load(f)
    
    func_code = None
    for const in code.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == 'test':
            func_code = const
            break
    
    if not func_code:
        print("  NO test function found!")
        return
    
    print("\n  BYTECODE:")
    for i in dis.get_instructions(func_code):
        print(f"    {i.offset:4d} {i.opname:35s} {i.argrepr}")
    
    from core.cfg.cfg_builder import CFGBuilder
    from core.cfg.dominator_analyzer import DominatorAnalyzer, LoopAnalyzer
    from core.cfg.region_analyzer import RegionAnalyzer
    
    builder = CFGBuilder()
    cfg = builder.build(func_code)
    
    print(f"\n  CFG BLOCKS ({len(cfg.blocks)}):")
    for block in cfg.blocks.values():
        inst = [f"{i.offset}:{i.opname}" for i in block.instructions[:5]]
        succ = [f"B{s.start_offset}" for s in block.successors]
        pred = [f"B{p.start_offset}" for p in block.predecessors]
        print(f"    B{block.start_offset:4d} [{', '.join(inst)}] → [{', '.join(succ)}] ← [{', '.join(pred)}]")
    
    dom = DominatorAnalyzer(cfg)
    
    print(f"\n  DOMINATOR TREE:")
    for block in cfg.blocks.values():
        idom = block.immediate_dominator
        print(f"    B{block.start_offset:4d} idom=B{idom.start_offset if idom else 'None'}")
    
    loop = LoopAnalyzer(cfg, dom)
    loop.analyze()
    
    print(f"\n  BACK EDGES:")
    for src, tgt in loop.back_edges:
        print(f"    B{src.start_offset} → B{tgt.start_offset} ({tgt.dominates(src)})")
    
    print(f"\n  LOOP HEADERS:")
    for hdr in loop.loop_headers:
        body = loop.loop_bodies.get(hdr, set())
        print(f"    B{hdr.start_offset}: body={[f'B{b.start_offset}' for b in body]}")
    
    analyzer = RegionAnalyzer(dom)
    regions = analyzer.run(cfg)
    
    print(f"\n  REGIONS ({len(regions)}):")
    for r in regions:
        print(f"    {r.region_type.name}: blocks={[f'B{b.start_offset}' for b in r.blocks]}")
        if hasattr(r, 'header_block') and r.header_block:
            print(f"      header=B{r.header_block.start_offset}, is_while_true={r.is_while_true}")
    
    from core.cfg.region_ast_generator import RegionASTGenerator
    gen = RegionASTGenerator(analyzer)
    result = gen.run(cfg)
    ast_str = gen.format_result(result)
    
    print(f"\n  DECOMPILED:")
    for line in ast_str.strip().split('\n'):
        print(f"    {line}")
    
    # Execute and compare
    # Strip comments
    lines = ast_str.split('\n')
    clean = []
    for line in lines:
        if line.startswith('# Source') or line.startswith('# File:'):
            continue
        clean.append(line)
    clean_src = '\n'.join(clean)
    
    try:
        ns = {}
        exec(compile(clean_src, '<decompiled>', 'exec'), ns)
        result = ns['test']()
        print(f"  DECOMPILED RESULT: {result}")
        
        # Original
        ns2 = {}
        with open(py_path, 'r') as f:
            orig = f.read()
        exec(compile(orig, '<orig>', 'exec'), ns2)
        expected = ns2['test']()
        print(f"  EXPECTED: {expected}")
        print(f"  MATCH: {result == expected}")
    except Exception as e:
        print(f"  ERROR: {e}")

debug_test('test_l04_while_break')
debug_test('test_l05_while_continue')
