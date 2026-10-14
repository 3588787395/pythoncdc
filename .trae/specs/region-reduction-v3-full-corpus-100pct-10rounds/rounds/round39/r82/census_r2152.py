"""[R21-52] 人口普查探针（惰性：只加日志，判据结果原样返回；产物必须与不挂探针时逐字节相同）。

usage: python -X utf8 census_r2152.py <pyc-abs> <log-path> <out-py>
"""
import marshal
import os
import sys

sys.path.insert(0, 'D:/Temp/r82')

LOG = sys.argv[2]
OUT = sys.argv[3]
tag = os.environ.get('R2152_TAG', os.path.basename(sys.argv[1]))

import core.cfg.region_ast_generator as rag  # noqa: E402
from core.cfg import build_cfg                        # noqa: E402
from core.cfg.region_ast_generator import RegionASTGenerator  # noqa: E402
from core.cfg.ast_converter import CFGASTConverter    # noqa: E402
from core.cfg.code_generator import CFGCodeGenerator  # noqa: E402

NOISE = ('RESUME', 'NOP', 'CACHE', 'EXTENDED_ARG')
COND_TERM = rag.FORWARD_CONDITIONAL_JUMP_OPS | rag.SHORT_CIRCUIT_JUMP_OPS | rag.NONE_CHECK_OPS


def _w(key):
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(key + '\n')


def off(b):
    return getattr(b, 'start_offset', None)


def r2152_member_refused(gen, blk):
    """[R21-52] 成员块资格判据（纯 opcode/栈形状，与实现里的判据逐行同构）：
    块末条件跳转消费的值若被更早的、把栈带回入口深度 0 的 POP_TOP 抢先消费，
    则该块内含一条完结语句 ⇒ 它不是布尔操作数 ⇒ 拒绝吸收。"""
    try:
        instrs = [i for i in (blk.instructions or [])]
        if not instrs:
            return False
        term = instrs[-1]
        if term.opname not in COND_TERM:
            return False
        depth = 0
        for ins in instrs[:-1]:
            if ins.opname in NOISE:
                continue
            eff = gen._instruction_stack_effect(ins)
            if eff is None:
                return False
            depth += eff
            if depth < 0:
                return False
            if ins.opname == 'POP_TOP' and depth == 0:
                return True
        return False
    except Exception:
        return False


_orig = rag._r2146_ibc_member_has_stmt_prefix
_cnt = {'eval': 0, 'fire': 0}


def _wrapped(gen, chain_blocks):
    r = _orig(gen, chain_blocks)
    _cnt['eval'] += 1
    if r:
        _cnt['fire'] += 1
    import inspect
    fr = inspect.stack()[1]
    _w('R2146CALL site=:%d blocks=%s ret=%s' % (
        fr.lineno, [off(b) if not isinstance(b, int) else b for b in (chain_blocks or [])], r))
    return r


rag._r2146_ibc_member_has_stmt_prefix = _wrapped

co = marshal.loads(open(sys.argv[1], 'rb').read()[16:])


def find_units(c, acc, prefix=''):
    acc.append((prefix + c.co_name, c))
    for cst in c.co_consts:
        if isinstance(cst, type(c)):
            find_units(cst, acc, prefix + c.co_name + '.')


units = []
find_units(co, units)
records = 0
members = 0
fired = 0
fired_not_r2146 = 0
for name, u in units:
    try:
        cfg = build_cfg(u)
        gen = RegionASTGenerator(cfg, parent_code=u if u.co_name != '<module>' else None,
                                 top_level_code=u if u.co_name == '<module>' else None)
        gen.generate()
    except Exception as e:
        _w('GEN-FAIL %s %r' % (name, e))
        continue
    for r in getattr(gen, 'regions', []) or []:
        ibc = getattr(r, 'inline_boolop_chains', None)
        if not ibc:
            continue
        for _k, ch in ibc.items():
            blocks = ch.get('blocks') or []
            head = off(blocks[0]) if blocks else None
            records += 1
            refused = []
            for b in blocks[1:]:
                members += 1
                if r2152_member_refused(gen, b):
                    refused.append(off(b))
            try:
                r2146_now = bool(_orig(gen, blocks))
            except Exception:
                r2146_now = None
            if refused:
                fired += 1
                if not r2146_now:
                    fired_not_r2146 += 1
                _w('FIRE unit=%s head=%s op=%s blocks=%s refused=%s r2146_pred=%s' % (
                    name, head, ch.get('op'), [off(b) for b in blocks], refused, r2146_now))
            else:
                _w('REC unit=%s head=%s op=%s blocks=%s refused=[] r2146_pred=%s' % (
                    name, head, ch.get('op'), [off(b) for b in blocks], r2146_now))
_w('CENSUS-LOOP file=%s records=%d members=%d fire_records=%d fire_only_new=%d' % (
   tag, records, members, fired, fired_not_r2146))
_cnt['eval'] = 0
_cnt['fire'] = 0

# 产物（与 pycdc.py --region 同一路径）：探针惰性证明用 —— 必须与不挂探针时逐字节相同
cfg = build_cfg(co)
_g = RegionASTGenerator(cfg, top_level_code=co)
source = CFGCodeGenerator().generate(CFGASTConverter().convert(_g.generate()))
with open(OUT, 'w', encoding='utf-8') as _f:
    _f.write("# Source Generated with Decompyle++ (Python version)\n")
    _f.write("# File: %s (Python 3.11)\n\n" % os.path.basename(sys.argv[1]))
    _f.write(source or '')
_w('SUMMARY file=%s records=%d members=%d fire_records=%d fire_only_new=%d '
   'r2146_eval=%d r2146_fire=%d' % (tag, records, members, fired, fired_not_r2146,
                                    _cnt['eval'], _cnt['fire']))
