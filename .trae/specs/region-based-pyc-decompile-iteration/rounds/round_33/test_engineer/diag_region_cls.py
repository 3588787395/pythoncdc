"""Round 33: 诊断 RegionASTGenerator 类体生成路径中的 NOP 处理。"""
import sys, marshal, types

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)
PYC = ROOT + r'\site-packages\fly\simtradding\ptradeAccount.pyc'


def load_code(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def main():
    pyc = load_code(PYC)
    cls = [c for c in pyc.co_consts if isinstance(c, types.CodeType) and c.co_name == 'PtradeAccount'][0]

    from core.cfg.cfg_builder import CFGBuilder
    from core.cfg.region_analyzer import RegionAnalyzer
    from core.cfg.region_ast_generator import RegionASTGenerator

    _b = CFGBuilder()
    cfg = _b.build(cls)
    print('CFG blocks:', len(cfg.blocks))

    an = RegionAnalyzer(cfg)
    regions = an.analyze()
    print('regions:', [(type(r).__name__) for r in regions])
    for r in regions:
        print('  %s entry=%s blocks=%d' % (type(r).__name__,
                                           r.entry.start_offset if r.entry else None,
                                           len(getattr(r, 'blocks', []))))

    gen = RegionASTGenerator(cfg, an)
    result = gen.generate()
    if isinstance(result, list):
        print('\n顶层语句数:', len(result))
        for s in result:
            print('  %-14s line=%s name=%s' % (s.get('type'), s.get('lineno'),
                                               s.get('name', s.get('id', ''))[:30]))
    elif isinstance(result, dict):
        body = result.get('body', [])
        print('\n顶层语句数:', len(body))
        for s in body:
            print('  %-14s line=%s name=%s' % (s.get('type'), s.get('lineno'),
                                               s.get('name', s.get('id', ''))[:30]))


if __name__ == '__main__':
    main()
