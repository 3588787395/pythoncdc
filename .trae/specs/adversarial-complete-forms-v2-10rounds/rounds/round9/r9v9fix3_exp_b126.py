"""Experiment variants for B126 assert_deep protocol-block ownership."""
import sys, os, marshal
sys.path.insert(0, os.path.abspath('.'))
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, AssertRegion, LoopRegion, BlockRole
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CFGCodeGenerator

def find(code, name):
    for c in code.co_consts:
        if hasattr(c, 'co_name'):
            if c.co_name == name:
                return c
            r = find(c, name)
            if r:
                return r

VARIANT = sys.argv[1] if len(sys.argv) > 1 else 'E1'
FUNC = sys.argv[2] if len(sys.argv) > 2 else 'assert_deep'
PYC = sys.argv[3] if len(sys.argv) > 3 else r'test_repros/round9/n9v9_stmt_sweep.pyc'
raw = marshal.loads(open(PYC, 'rb').read()[16:])
code = find(raw, FUNC)
from core.cfg.region_analyzer import RegionType

orig_dbc = RegionAnalyzer._detect_break_continue
def dbc_wrap(self, loop_body, header, natural_exit=None, natural_back_edge=None,
             condition_block=None, for_iter_exit=None, else_blocks=None):
    bb, cm = orig_dbc(self, loop_body, header, natural_exit, natural_back_edge,
                      condition_block, for_iter_exit, else_blocks)
    if VARIANT in ('E4', 'E6'):
        from core.cfg.region_analyzer import (NOISE_OPS, CONDITIONAL_JUMP_OPS,
                                              SHORT_CIRCUIT_JUMP_OPS)
        body_set = set(loop_body)
        _else_set = set(else_blocks) if else_blocks else set()

        def _pure_cleanup(b):
            return not [i for i in b.instructions
                        if i.opname not in NOISE_OPS
                        and i.opname not in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT',
                                             'JUMP_FORWARD', 'JUMP_ABSOLUTE')
                        and i.opname not in CONDITIONAL_JUMP_OPS
                        and i.opname not in SHORT_CIRCUIT_JUMP_OPS
                        and i.opname not in ('POP_TOP', 'EXTENDED_ARG')]

        def _raise_only_exit(s):
            cur = s
            seen = {s}
            for _ in range(8):
                if any(i.opname in ('RAISE_VARARGS', 'RERAISE') for i in cur.instructions):
                    R = cur
                    if (R in body_set or R == header or R == natural_exit
                            or R == for_iter_exit or R == condition_block
                            or R in _else_set):
                        return False
                    for p in R.predecessors:
                        if p is R or p in seen:
                            continue
                        if (p in body_set or p == header or p == natural_exit
                                or p == for_iter_exit or p == condition_block
                                or p in _else_set):
                            return False
                        if not _pure_cleanup(p):
                            return False
                    return True
                if not _pure_cleanup(cur):
                    return False
                nxt = [x for x in cur.successors if x is not cur
                       and x not in getattr(cur, 'exception_successors', set())
                       and x not in seen]
                if len(nxt) != 1:
                    return False
                cur = nxt[0]
                seen.add(cur)
            return False
        bb = {b for b in bb if not _raise_only_exit(b)}
    return bb, cm
RegionAnalyzer._detect_break_continue = dbc_wrap

orig_analyze = RegionAnalyzer.analyze
def analyze_wrap(self):
    r = orig_analyze(self)
    cfg = self.cfg
    a_region = None
    for reg in self.regions:
        if isinstance(reg, AssertRegion):
            a_region = reg
            break
    f_region = None
    for reg in self.regions:
        if isinstance(reg, LoopRegion) and reg.region_type == RegionType.FOR_LOOP:
            f_region = reg
            break
    if VARIANT in ('E4', 'E6') and f_region is not None:
        print('[E4] for break_blocks after guard:',
              [b.start_offset for b in f_region.break_blocks],
              'has_break:', f_region.has_break,
              'roles:', {b.start_offset: self.block_roles.get(b.start_offset)
                         for b in f_region.blocks if self.block_roles.get(b.start_offset) is not None
                         and str(self.block_roles.get(b.start_offset)) != 'BlockRole.LOOP_BODY'})
    if FUNC != 'assert_deep':
        return r
    b74 = cfg.get_block_by_offset(74)
    b76 = cfg.get_block_by_offset(76)
    if VARIANT in ('E1', 'E1b', 'E4'):
        assert a_region is not None
        a_region.blocks.add(b74); a_region.blocks.add(b76)
        self.block_to_region[b74] = a_region
        self.block_to_region[b76] = a_region
    if VARIANT == 'E1b':
        f_region.break_blocks = [b for b in f_region.break_blocks if b.start_offset not in (74, 76)]
        f_region.has_break = bool(f_region.break_blocks)
        self.block_roles[74] = BlockRole.LOOP_BODY
        self.block_roles[76] = BlockRole.LOOP_BODY
    if VARIANT == 'E3':
        assert a_region is not None
        a_region.entry = None
        self.regions.remove(a_region)
        for b in list(a_region.blocks):
            if self.block_to_region.get(b) is a_region:
                del self.block_to_region[b]
        # keep entry ownership with parent loop (48 is while header)
        while_reg = None
        for reg in self.regions:
            if isinstance(reg, LoopRegion) and reg.entry.start_offset == 34:
                while_reg = reg
        if while_reg is not None:
            self.block_to_region[a_region.condition_block] = while_reg
    return r
RegionAnalyzer.analyze = analyze_wrap

cfg = build_cfg(code)
gen = RegionASTGenerator(cfg)
ast_dict = gen.generate()
converter = CFGASTConverter()
py_ast = converter.convert(ast_dict)
code_gen = CFGCodeGenerator()
source = code_gen.generate(py_ast)
print('===== VARIANT %s =====' % VARIANT)
print(source)
