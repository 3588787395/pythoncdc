"""Round 33 回归诊断：time_validator.can_cancel_order 的 is_listing 判断丢失。

region 层 then=[140,202] 正确，但 AST 层 140（is_listing 条件块）生成空。
本脚本打印 region 树、inline_boolop_chains、then_blocks 明细，并跟踪
AST 生成时各块的消费情况。
"""
import sys, marshal, types

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)
PYC = ROOT + r'\site-packages\IQEngine\plugins\plugin_system_risk_control\time_validator.pyc'


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
    pyc = load_code(PYC)
    fn = find_code(pyc, 'can_cancel_order')

    from core.cfg.cfg_builder import CFGBuilder
    from core.cfg.region_analyzer import RegionAnalyzer
    from core.cfg.region_ast_generator import RegionASTGenerator

    _b = CFGBuilder()
    cfg = _b.build(fn)
    print('CFG blocks: %d' % len(cfg.blocks))
    for blk in cfg.get_blocks_in_order():
        last = blk.get_last_instruction()
        print('  blk@%-5d last=%-30s succ=%s' % (
            blk.start_offset,
            last.opname if last else 'None',
            [s.start_offset for s in blk.successors]))

    an = RegionAnalyzer(cfg)
    regions = an.analyze()
    print('\nregions: %d' % len(regions))
    for r in regions:
        ibc = getattr(r, 'inline_boolop_chains', None)
        info = ''
        if ibc:
            for k, v in ibc.items():
                info += ' ibc{%s: op=%s blocks=%s}' % (
                    k, v.get('op'), [b.start_offset for b in v.get('blocks', [])])
        print('  %-12s entry=%-5s blocks=%s then=%s else=%s merge=%s%s' % (
            type(r).__name__,
            r.entry.start_offset if r.entry else None,
            [b.start_offset for b in (getattr(r, 'blocks', None) or [])],
            [b.start_offset for b in getattr(r, 'then_blocks', []) or []],
            [b.start_offset for b in getattr(r, 'else_blocks', []) or []],
            r.merge_block.start_offset if getattr(r, 'merge_block', None) else None,
            info))

    gen = RegionASTGenerator(cfg, an)
    # hook: 记录生成期间哪些块被消费
    orig_gen = gen._generate_region

    def patched(region):
        offs = getattr(region, 'blocks', None)
        print('  [gen] %s entry=%s blocks=%s' % (
            type(region).__name__,
            region.entry.start_offset if region.entry else None,
            [b.start_offset for b in (offs or [])][:12]))
        return orig_gen(region)

    gen._generate_region = patched
    result = gen.generate()
    print('\nAST result type:', type(result).__name__)
    body = result.get('body', []) if isinstance(result, dict) else result
    for s in body:
        print('  %-12s line=%s' % (s.get('type'), s.get('lineno')))


if __name__ == '__main__':
    main()
