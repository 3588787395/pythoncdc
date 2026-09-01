"""Round 33: 走完整管道 (ASTGeneratorV2 -> CFGASTConverter -> CFGCodeGenerator)，
定位占位 Expr 在类体渲染中的丢失点。"""
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

    from core.cfg.cfg_builder import build_cfg
    from core.cfg.ast_generator_v2 import ASTGeneratorV2
    from core.cfg.ast_converter import CFGASTConverter
    from core.cfg.code_generator import CFGCodeGenerator

    # 1) ASTGeneratorV2 生成 dict AST
    cfg = build_cfg(cls, 'PtradeAccount')
    gen = ASTGeneratorV2(cfg, recursive=True)
    ast_dict = gen.generate()
    body = ast_dict.get('body', [])
    print('dict AST 顶层节点:', len(body))
    nop_marks = [n for n in body if n.get('_nop_placeholder')]
    print('dict AST 中占位节点:', len(nop_marks))

    # 2) CFGASTConverter 转换
    conv = CFGASTConverter()
    py_ast = conv.convert(ast_dict)
    from core.ast_nodes import ASTClassDef, ASTExpr, ASTConstant
    if isinstance(py_ast, ASTClassDef):
        print('\nASTClassDef body 节点数:', len(py_ast.body))
        exprs = [n for n in py_ast.body if isinstance(n, ASTExpr)]
        print('body 中 ASTExpr 节点数:', len(exprs))
        for e in exprs[:10]:
            print('  ASTExpr value=%r' % (e.value.value if isinstance(e.value, ASTConstant) else type(e.value)))
    else:
        print('转换结果类型:', type(py_ast))

    # 3) CFGCodeGenerator 生成源码
    cg = CFGCodeGenerator()
    src = cg.generate(py_ast, in_function=False)
    if src:
        lines = src.splitlines()
        empties = [i + 1 for i, l in enumerate(lines) if l.strip() in ('""', "''")]
        print('\n生成源码行数:', len(lines), '独立空字符串行:', len(empties), empties[:10])
        # 打印类体附近的行
        for ln in empties[:6]:
            print('  L%d: %r' % (ln, lines[ln - 1]))


if __name__ == '__main__':
    main()
