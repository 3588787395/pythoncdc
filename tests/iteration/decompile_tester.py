import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator
import ast
import textwrap
import traceback
import types
import dis


def decompile_source(source: str, mode: str = 'exec') -> str:
    code = compile(source, '<test>', mode)
    cfg = CFGBuilder().build(code)
    analyzer = RegionAnalyzer(cfg)
    generator = RegionASTGenerator(cfg, analyzer)
    result = generator.generate()
    code_gen = CodeGenerator()
    return code_gen.generate(result)


def verify_decompilation(source: str, mode: str = 'exec') -> dict:
    """
    Returns dict with keys:
      'ok': bool
      'decompiled': str
      'error': str or None
      'category': 'syntax_error' | 'ast_mismatch' | 'bytecode_mismatch' | 'exception' | None
      'expected_ast_type': str or None (e.g. 'If')
      'actual_ast_types': list of str
    """
    result = {'ok': False, 'decompiled': '', 'error': None, 'category': None,
              'expected_ast_type': None, 'actual_ast_types': []}
    try:
        code = compile(source, '<test>', mode)
    except SyntaxError as e:
        result['error'] = f'SyntaxError in source: {e}'
        result['category'] = 'syntax_error'
        return result

    try:
        cfg = CFGBuilder().build(code)
        analyzer = RegionAnalyzer(cfg)
        generator = RegionASTGenerator(cfg, analyzer)
        ast_result = generator.generate()
        code_gen = CodeGenerator()
        decompiled = code_gen.generate(ast_result)
        result['decompiled'] = decompiled
    except Exception as e:
        result['error'] = f'Decompilation exception: {traceback.format_exc()}'
        result['category'] = 'exception'
        return result

    try:
        recompiled = compile(decompiled, '<decompiled>', mode)
    except SyntaxError as e:
        result['error'] = f'SyntaxError in decompiled output: {e}\nOutput:\n{decompiled}'
        result['category'] = 'syntax_error'
        return result

    orig_instrs = _filter_jumps(list(dis.get_instructions(code)))
    recomp_instrs = _filter_jumps(list(dis.get_instructions(recompiled)))
    mismatch = _compare_instructions(orig_instrs, recomp_instrs)
    if mismatch:
        result['error'] = f'Bytecode mismatch: {mismatch}\nDecompiled:\n{decompiled}'
        result['category'] = 'bytecode_mismatch'
        return result

    result['ok'] = True
    return result


def _filter_jumps(instrs):
    skip = {
        'JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE',
        'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
        'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
        'FOR_ITER', 'SEND', 'NOP', 'CACHE',
    }
    return [i for i in instrs if i.opname not in skip]


def _compare_instructions(orig, recomp, depth=0):
    if depth > 5:
        return None
    if len(orig) != len(recomp):
        return f'Instruction count: {len(orig)} vs {len(recomp)}'
    for i, (o, r) in enumerate(zip(orig, recomp)):
        if o.opname != r.opname:
            return f'Op #{i}: {o.opname} vs {r.opname}'
        if o.argval != r.argval and o.opname not in (
            'JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE',
            'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
        ):
            if isinstance(o.argval, types.CodeType) and isinstance(r.argval, types.CodeType):
                sub = _compare_instructions(
                    _filter_jumps(list(dis.get_instructions(o.argval))),
                    _filter_jumps(list(dis.get_instructions(r.argval))),
                    depth + 1)
                if sub:
                    return f'Nested code object mismatch (#{i}): {sub}'
            else:
                try:
                    if abs(o.argval or 0) != abs(r.argval or 0):
                        return f'Arg #{i}: {o.argval} vs {r.argval} (op={o.opname})'
                except TypeError:
                    if o.argval != r.argval:
                        return f'Arg #{i}: {o.argval} vs {r.argval} (op={o.opname})'
    return None
