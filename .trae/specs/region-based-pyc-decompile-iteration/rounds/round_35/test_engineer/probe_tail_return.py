"""R35 探针:验证 _generate_stmts_from_instrs 能否重建尾部 return (a, b)。

blk@300 中 STORE_FAST source_end 之后的 4 条指令:
  LOAD_FAST source_start | LOAD_FAST source_end | BUILD_TUPLE 2 | RETURN_VALUE
"""
import sys, marshal, types, json
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')

ROOT = r"F:\Downloads\pythoncdc-main"
PYC = ROOT + r'\site-packages\IQCommon\util\datetime_func.pyc'
FN = 'change_2str_of_time_2_datetime'


def load_code(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def find_code(co, name):
    if co.co_name == name:
        return co
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            r = find_code(c, name)
            if r:
                return r
    return None


def main():
    from core.cfg.cfg_builder import CFGBuilder
    from core.cfg.region_analyzer import RegionAnalyzer
    from core.cfg.region_ast_generator import RegionASTGenerator

    pyc = load_code(PYC)
    fn = find_code(pyc, FN)

    _b = CFGBuilder()
    cfg = _b.build(fn)
    blk300 = cfg.get_block_by_offset(300)
    print('blk300 instrs:')
    for i in blk300.instructions:
        print('  @%d %s %s' % (i.offset, i.opname, i.argval if i.argval is not None else ''))

    an = RegionAnalyzer(cfg)
    regions = an.analyze()
    print('\nregions: %d' % len(regions))
    for r in regions:
        print('  %-16s entry=%-5s blocks=%s merge=%s' % (
            type(r).__name__,
            r.entry.start_offset if getattr(r, 'entry', None) else None,
            [b.start_offset for b in (getattr(r, 'blocks', None) or [])],
            getattr(r, 'merge_block', None).start_offset if getattr(r, 'merge_block', None) else None))
    # 是否存在 entry=300 的普通 Region?
    for r in regions:
        if getattr(r, 'entry', None) is blk300 and type(r).__name__ == 'Region':
            print('\nDEGENERATE Region(300) FOUND: blocks=%s' % [b.start_offset for b in r.blocks])
            print('is only block? %s' % (set(r.blocks) == {blk300}))

    gen = RegionASTGenerator(cfg, an)
    tail = [i for i in blk300.instructions
            if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
    # 定位 STORE 之后的指令
    store_idx = next(i for i, ins in enumerate(tail) if ins.opname == 'STORE_FAST')
    post = tail[store_idx + 1:]
    print('\npost-store instrs: %s' % [(i.opname, i.argval) for i in post])

    stmts = gen._generate_stmts_from_instrs(post, blk300)
    print('\n_generate_stmts_from_instrs -> %d stmts' % len(stmts))
    for s in stmts:
        print(json.dumps(s, ensure_ascii=False, default=str)[:400])


if __name__ == '__main__':
    main()
