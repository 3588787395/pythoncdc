import sys, marshal, types, dis, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')

from core.cfg.cfg_builder import build_cfg, CFGBuilder

pyc = 'F:/Downloads/pythoncdc-main/site-packages/IQCommon/util/replace_utils.pyc'
with open(pyc, 'rb') as f:
    f.read(16); orig = marshal.load(f)

def extract(co):
    r = {}; r[co.co_name or '<module>'] = co
    for c in co.co_consts:
        if isinstance(c, types.CodeType): r.update(extract(c))
    return r

om = extract(orig)
code = om['decrypt_database_url']
cfg = build_cfg(code)

print(f"Function: decrypt_database_url")
print(f"Number of blocks: {len(cfg.blocks)}")
print()

for block in cfg.get_blocks_in_order():
    if True:
        last = block.get_last_instruction()
        last_str = f"{last.opname} {last.arg}" if last else "None"
        succs = [f"blk@{s.start_offset}" for s in block.successors]
        cond_succs = [f"blk@{s.start_offset}" for s in block.conditional_successors]
        print(f"Block@{block.start_offset}-{block.end_offset} last={last_str} succs={succs} cond_succs={cond_succs}")
        for instr in block.instructions:
            a = f'{instr.arg}' if instr.arg is not None else ''
            print(f'  {instr.offset:4d} {instr.opname:35s} {a}')
        print()
