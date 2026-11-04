# rr-v5r112 诊断插桩：区域树 dump + 各 BoolOp hook 返回值 + 最终 AST 里
# 所有 UnaryOp(not) 节点路径。只读诊断，不改任何产品源码。
import sys, os, json, marshal
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
os.chdir('F:/Downloads/pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg import region_analyzer as RA

EV = 'F:/Downloads/pythoncdc-main/.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/notboolop_orand'
DIAG = 'D:/temp/opencode/cl_layout/r112diag_b'

def J(x):
    return json.dumps(x, ensure_ascii=False, default=str)

def find_not(node, path='', out=None):
    if out is None:
        out = []
    if isinstance(node, dict):
        if node.get('type') == 'UnaryOp' and node.get('op') in ('not', 'Not'):
            out.append((path, J(node)[:500]))
        for k, v in node.items():
            find_not(v, path + '/' + str(k), out)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            find_not(v, path + '/' + str(i), out)
    return out

LOG = []

def dump_regions(gen):
    regs = getattr(gen.region_analyzer, 'regions', None) or []
    for r in regs:
        if isinstance(r, RA.BoolOpRegion):
            oc = getattr(r, 'op_chain', None) or []
            def li(b):
                i = b.get_last_instruction()
                return (i.opname, i.argval) if i else None
            log = '  BoolOpRegion entry=@%s merge=@%s value_target=%s cond_ctx=%s' % (
                getattr(r, 'entry', None).start_offset if getattr(r, 'entry', None) else '?',
                r.merge_block.start_offset if getattr(r, 'merge_block', None) else '?',
                getattr(r, 'value_target', '?'),
                getattr(r, 'is_condition_context', '?'))
            LOG.append(log)
            LOG.append('    op_chain=%s' % [(b.start_offset, op, li(b)) for b, op in oc])
            mb = getattr(r, 'merge_block', None)
            if mb:
                LOG.append('    merge_instrs=%s' % [i.opname for i in mb.instructions
                                                     if i.opname not in ('RESUME', 'NOP', 'CACHE')])

# ---- patch 类方法（覆盖嵌套生成器实例）----
_orig_generate = RegionASTGenerator.generate
def w_generate(self):
    LOG.append('=== GENERATE cfg.name=%s ===' % self.cfg.name)
    r = _orig_generate(self)
    dump_regions(self)
    for p, n in find_not(r):
        LOG.append('  [AST-NOT] %s : %s' % (p, n))
    return r
RegionASTGenerator.generate = w_generate

HOOKS = ['_build_boolop_expression', '_build_boolop_expression_inner',
         '_try_build_keeppop_target_grouped', '_build_grouped_boolop_expression',
         '_build_boolop_skipedge_grouped', '_try_build_and_inner_or_pattern']
for _h in HOOKS:
    _f = getattr(RegionASTGenerator, _h)
    def _mk(name, f):
        def w(self, *a, **kw):
            r = f(self, *a, **kw)
            LOG.append('  [HOOK %s] cfg=%s -> %s' % (name, self.cfg.name, J(r)[:600] if r is not None else 'None'))
            return r
        return w
    setattr(RegionASTGenerator, _h, _mk(_h, _f))

CASES = ['m4_not', 'm5_hash', 'm8_getfield', 'm2_orand', 'm3_getfield']
for name in CASES:
    LOG = []
    pyc = DIAG + '/%s.pyc' % name
    code = marshal.loads(open(pyc, 'rb').read()[16:])
    cfg = build_cfg(code)
    gen = RegionASTGenerator(cfg, top_level_code=code if code.co_name == '<module>' else None)
    try:
        gen.generate()
    except Exception as e:
        LOG.append('EXCEPTION: %r' % e)
    out = EV + '/probe_%s.txt' % name
    open(out, 'w', encoding='utf-8').write('\n'.join(LOG) + '\n')
    print('%s -> %s (%d lines)' % (name, out, len(LOG)))
