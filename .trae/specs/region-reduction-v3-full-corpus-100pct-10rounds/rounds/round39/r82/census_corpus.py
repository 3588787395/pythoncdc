"""[R21-52] 语料级判据面普查（只跑分析端，不生成 AST；纯只读，不改任何字节）。

对每个 .pyc 的每个 code object：RegionAnalyzer(cfg).analyze() → 枚举全部
IfRegion.inline_boolop_chains 记录 → 对每个成员块算 [R21-52] 资格判据 与
[R21-46] 的「未发射语句前导」判据所需的切分器结果（前缀存在性，台账除外）。

usage: python -X utf8 census_corpus.py <roster-file|all>
"""
import dis
import marshal
import os
import sys

sys.path.insert(0, 'D:/Temp/r82')

from core.cfg import build_cfg                                   # noqa: E402
from core.cfg.region_analyzer import RegionAnalyzer              # noqa: E402
import core.cfg.region_ast_generator as rag                      # noqa: E402

SP = 'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/site-packages/'
NOISE = ('RESUME', 'NOP', 'CACHE', 'EXTENDED_ARG')
COND_TERM = rag.FORWARD_CONDITIONAL_JUMP_OPS | rag.SHORT_CIRCUIT_JUMP_OPS | rag.NONE_CHECK_OPS


def stack_effect(ins):
    try:
        return dis.stack_effect(ins.opcode, ins.arg)
    except (ValueError, TypeError):
        pass
    try:
        return dis.stack_effect(ins.opcode)
    except (ValueError, TypeError):
        return None


def member_refused(blk):
    """[R21-52] 资格判据（与 generator 里实现的那一份逐行同构）。"""
    instrs = list(blk.instructions or [])
    if not instrs:
        return False
    if instrs[-1].opname not in COND_TERM:
        return False
    depth = 0
    for ins in instrs[:-1]:
        if ins.opname in NOISE:
            continue
        eff = stack_effect(ins)
        if eff is None or depth + eff < 0:
            return False
        depth += eff
        if ins.opname == 'POP_TOP' and depth == 0:
            return True
    return False


def has_stmt_prefix(blk):
    """[R21-46] 的切分器半边（不看 prefix_emitted_upto 台账）：块内是否存在栈已归零的前导段。"""
    instrs = list(blk.instructions or [])
    if not instrs:
        return False
    if instrs[-1].opname not in (rag.FORWARD_CONDITIONAL_JUMP_OPS | rag.NONE_CHECK_OPS):
        return False
    depth = 0
    last_zero = -1
    for idx, ins in enumerate(instrs[:-1]):
        eff = rag.RegionASTGenerator._instruction_stack_effect(ins)
        if eff is None or depth + eff < 0:
            return False
        depth += eff
        if depth == 0:
            last_zero = idx
    if last_zero < 0:
        return False
    pfx = instrs[:last_zero + 1]
    return not all(i.opname in NOISE for i in pfx)


_gen = None


def walk(c, acc, prefix=''):
    acc.append((prefix + c.co_name, c))
    for cst in c.co_consts:
        if isinstance(cst, type(c)):
            walk(cst, acc, prefix + c.co_name + '.')


def off(b):
    return getattr(b, 'start_offset', None)


files = []
for dirpath, dirnames, filenames in os.walk(SP):
    if '__pycache__' in dirpath.replace('\\', '/').split('/'):
        continue
    for fn in filenames:
        if fn.endswith('.pyc'):
            files.append(os.path.join(dirpath, fn))
files.sort()
print('files=%d' % len(files))

tot_rec = tot_mem = tot_fire = tot_fire_only_new = tot_fire_no_prefix = 0
hits = []
bad = 0
for i, path in enumerate(files):
    try:
        co = marshal.loads(open(path, 'rb').read()[16:])
    except Exception:
        bad += 1
        continue
    units = []
    walk(co, units)
    f_rec = f_mem = f_fire = 0
    for name, u in units:
        try:
            cfg = build_cfg(u)
            an = RegionAnalyzer(cfg, top_level_code=u if u.co_name == '<module>' else None,
                                parent_code=None if u.co_name == '<module>' else u)
            regions = an.analyze()
        except Exception:
            continue
        for r in regions:
            for ch in (getattr(r, 'inline_boolop_chains', None) or {}).values():
                blocks = ch.get('blocks') or []
                if not blocks:
                    continue
                f_rec += 1
                refused = []
                prefixed = []
                for b in blocks[1:]:
                    f_mem += 1
                    if member_refused(b):
                        refused.append(off(b))
                    if has_stmt_prefix(b):
                        prefixed.append(off(b))
                if refused:
                    f_fire += 1
                    hits.append('%s :: %s head=%s op=%s blocks=%s refused=%s r2146prefix=%s' % (
                        path[len(SP):].replace('\\', '/'), name, off(blocks[0]), ch.get('op'),
                        [off(b) for b in blocks], refused, prefixed))
                    if not prefixed:
                        tot_fire_no_prefix += 1
    tot_rec += f_rec
    tot_mem += f_mem
    tot_fire += f_fire
    if f_fire:
        print('%-70s rec=%d mem=%d fire=%d' % (path[len(SP):].replace('\\', '/'), f_rec,
                                               f_mem, f_fire))
print('UNREADABLE=%d' % bad)
print('CORPUS records=%d members=%d fire_records=%d fire_without_r2146_prefix=%d' % (
    tot_rec, tot_mem, tot_fire, tot_fire_no_prefix))
for h in hits:
    print('HIT ' + h)
