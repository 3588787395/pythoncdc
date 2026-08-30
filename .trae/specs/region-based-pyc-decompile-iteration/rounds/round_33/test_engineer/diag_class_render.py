"""Round 33: 调试 _generate_class_def 输出，定位 ASTExpr('') 的渲染去向。"""
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
    from core.ast_nodes import ASTClassDef, ASTExpr, ASTConstant

    cfg = build_cfg(cls, 'PtradeAccount')
    gen = ASTGeneratorV2(cfg, recursive=True)
    ast_dict = gen.generate()
    conv = CFGASTConverter()
    py_ast = conv.convert(ast_dict)

    cg = CFGCodeGenerator()

    # 手动复刻 _generate_class_def 的过滤链
    body_list = py_ast.body if isinstance(py_ast.body, list) else []
    print('body 原始节点数:', len(body_list))
    f1 = cg._filter_return_nodes(body_list)
    print('filter_return_nodes 后:', len(f1))
    f2 = cg._filter_class_internal_assigns(f1)
    print('filter_class_internal_assigns 后:', len(f2))
    exprs = [n for n in f2 if isinstance(n, ASTExpr)]
    print('过滤后 ASTExpr 数:', len(exprs))
    for e in exprs:
        print('   ASTExpr value=%r type=%s' % (
            e.value.value if isinstance(e.value, ASTConstant) else None, type(e.value).__name__))

    # 直接用 _generate_class_def 生成源码
    import io
    buf = io.StringIO()
    cg._output = buf
    cg._indent = 0
    cg._write_line = lambda line: buf.write('    ' * cg._indent + line + '\n')
    # 更稳妥：直接调用类体部分生成
    cg._increase_indent = lambda: setattr(cg, '_indent', cg._indent + 1)
    cg._decrease_indent = lambda: setattr(cg, '_indent', cg._indent - 1)
    # 手动跑 L2566-2579 逻辑
    body_list2 = py_ast.body
    filtered_nodes = cg._filter_return_nodes(body_list2)
    filtered_nodes = cg._filter_class_internal_assigns(filtered_nodes)
    from core.ast_nodes import ASTBlock
    cg._indent = 1
    if filtered_nodes:
        cg._generate_block(ASTBlock(filtered_nodes))
    out = buf.getvalue()
    lines = out.splitlines()
    print('\n类体渲染行数:', len(lines))
    triple = [i + 1 for i, l in enumerate(lines) if l.strip() == '""""""' or l.strip() == "''''''"]
    print('三引号空串行:', len(triple), triple)
    empties = [i + 1 for i, l in enumerate(lines) if l.strip() in ('""', "''")]
    print('双引号空串行:', len(empties), empties)
    # 打印 ASTExpr 前后的行
    for ln in (triple + empties)[:6]:
        print('  上下文 L%d-%d:' % (max(1, ln - 1), min(len(lines), ln + 1)))
        for j in range(max(0, ln - 2), min(len(lines), ln + 1)):
            print('     %r' % lines[j])


if __name__ == '__main__':
    main()
