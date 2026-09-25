# -*- coding: utf-8 -*-
"""diag1 r67: profiler-based call tree of the generator for ONE function.

usage: python -X utf8 ctr.py <pyc> <func> <watch_offset[,offset...]>
Records every call whose first Region-like argument has entry offset in WATCH,
so we can see WHICH method generates the join region while still inside the
parent's then-branch emission.
"""
import io
import marshal
import os
import sys
import types

sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
os.chdir(r'F:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')
from blk import load_pyc, walk, off  # noqa: E402

GEN = os.path.abspath('core/cfg/region_ast_generator.py').replace('\\', '/')
WATCH = set()
OUT = []


def region_arg(frame):
    for k, v in list(frame.f_locals.items()):
        e = getattr(v, 'entry', None)
        if e is not None and hasattr(e, 'instructions') and hasattr(v, 'blocks'):
            return type(v).__name__, off(e)
    return None


def tracer(frame, event, arg):
    if frame.f_code.co_filename.replace('\\', '/') != GEN:
        return None
    if event != 'call':
        return tracer
    name = frame.f_code.co_name
    ra = region_arg(frame)
    if ra and ra[1] in WATCH:
        OUT.append(('C', depth[0], name, ra[0], ra[1]))
        depth[0] += 1
        return tracer
    if ra:
        return tracer
    return tracer


depth = [0]


def main(pyc, name, watch):
    global WATCH
    WATCH = set(int(x) for x in watch.split(',') if x.strip())
    co = [c for c in walk(load_pyc(pyc), []) if c.co_name == name][0]
    import dis
    import core.cfg.ast_converter as A
    from core.decompiler_context import DecompilerContext
    from core.bytecode_executor.dynamic_code_analyzer import DynamicCodeAnalyzer
    from core.bytecode_executor.instruction_formatter import InstructionFormatter
    from core.bytecode_executor.code_object_transformer import CodeObjectTransformer
    from core.bytecode_executor.module_structure_builder import ModuleStructureBuilder
    from core.bytecode_executor.exception_table_parser import ExceptionTableParser
    from core.bytecode_executor.hierarchical_decompiles import HierarchicalSubcodeDecompiler
    from core.utils.text_utils import truncate_error_message
    from core.cfg.region_ast_generator import generate_ast_from_cfg
    mb = ModuleStructureBuilder()
    et = ExceptionTableParser()
    outer = mb.build_module_node_for_code(co, {'type': 'Module', 'name': co.co_name,
                                               'docstring': None, 'body': []})
    dc = {'type': 'Code', 'name': 'dummy_func', 'docstring': None,
          'parameters': {'posonly': [], 'kwonly': [], 'vararg': None, 'kwarg': None},
          'code': {'type': 'Bytecode', 'bytecode_ops': list(dis.get_instructions(co)),
                   'exception_table': et.get_parsed_exception_table(co), 'consts': co.co_consts}}
    fa = DynamicCodeAnalyzer(InstructionFormatter(), CodeObjectTransformer())
    fn = fa.analyze_code_structure(dc, co)
    inner = fn if isinstance(fn, dict) else dc
    hs = HierarchicalSubcodeDecompiler(DecompilerContext(), InstructionFormatter(),
                                        CodeObjectTransformer())
    ctx = {'module_node': outer, 'current_frame': {'code': co}, 'is_top_level': True}
    sys.setprofile(tracer)
    try:
        ast = generate_ast_from_cfg(co, fallback_func=mb.build_module_node_for_code,
                                    current_frame=inner, decompiled_children=hs._cache,
                                    top_level_code=co, context=ctx)
    finally:
        sys.setprofile(None)
    io.open('logs/ast_%s.py' % name, 'w', encoding='utf-8').write(A.ast_to_python_code(ast)[0])
    print('== CALL TREE (watch=%s) ==' % sorted(WATCH))
    for ev, d, nm, rn, eo in OUT:
        print('%s%-40s %s@%d' % ('  ' * d, nm, rn, eo))
    print('total watched frames', len(OUT))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
