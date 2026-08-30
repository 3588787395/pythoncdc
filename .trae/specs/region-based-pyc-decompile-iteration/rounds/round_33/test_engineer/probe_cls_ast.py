"""Round 33: 探查类体 CFG -> AST 生成路径，定位 NOP 处理。"""
import sys, marshal, types, json

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
    print('类体 co_code len:', len(cls.co_code))

    # 1) 用 CFG 构建类体
    from core.cfg.cfg_builder import build_cfg
    cfg = build_cfg(cls, 'PtradeAccount')
    blocks = cfg.get_blocks_in_order()
    print('CFG blocks:', len(blocks))
    # dump 包含 NOP 的块
    for b in blocks:
        for ins in b.instructions:
            if ins.opname == 'NOP':
                print('NOP 所在块:', b.start_offset, '->', b.end_offset, '块内指令:')
                for i in b.instructions:
                    print('   ', i.offset, i.opname, i.argval, 'line=', i.starts_line)

    # 2) 生成 AST，看顶层节点
    from core.cfg.ast_generator_v2 import ASTGeneratorV2
    gen = ASTGeneratorV2(cfg, recursive=True)
    ast = gen.generate()
    print()
    print('AST 顶层节点数:', len(ast.get('body', [])))
    for n in ast.get('body', []):
        t = n.get('type')
        nm = n.get('name', n.get('id', ''))
        ln = n.get('lineno')
        print('  %-14s %-30s line=%s' % (t, str(nm)[:30], ln))


if __name__ == '__main__':
    main()
