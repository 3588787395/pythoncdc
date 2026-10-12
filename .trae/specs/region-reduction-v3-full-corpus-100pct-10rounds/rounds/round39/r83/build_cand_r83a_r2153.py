"""R21-53 candidate builder — elif **collection** refusal keyed on the shared false-exit block.

Base (byte-level whole-file rebuild, never a hand-edited *OK.py):
    REPO/.trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/rounds/round39/r75/
      CANDIDATE_r75a_r2146_AB_on_r74d_30a4d7827122e165.py   sha256[:16] = 30a4d7827122e165
  (that is the GENERATOR base; this ticket patches the ANALYZER, which stays at landed
   f7d849e974904492 unless --fix/--probe is applied to it.)

Modes
  --probe   record-only census hook in core/cfg/region_analyzer.py `_check_elif_chain`
            (products MUST be byte-identical to base; proves the probe inert, rule 2)
  --fix      [R21-53] narrow refusal: drop ONLY the mis-collected elif condition (and its
            paired body) whose false exit is a block the parent arm declares as its body and
            that this same chain simultaneously declares in elif_final_else.
            `final_else` is NOT touched — the chain keeps its tail ownership (the [R21-49]
            -269 failure mode was dereofusing the whole chain).

usage:
  python -X utf8 build_cand_r83a_r2153.py --probe  --out <path>
  python -X utf8 build_cand_r83a_r2153.py --fix    --out <path>
  python -X utf8 build_cand_r83a_r2153.py --base   --out <path>   # byte-exact base copy
"""
import hashlib
import os
import py_compile
import shutil
import sys

REPO = 'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main'
SPEC = REPO + '/.trae/specs/region-reduction-v3-full-corpus-100pct-10rounds'
BASE_GEN = SPEC + '/rounds/round39/r75/CANDIDATE_r75a_r2146_AB_on_r74d_30a4d7827122e165.py'
BASE_GEN_SHA16 = '30a4d7827122e165'
ANALYZER_LANDED_SHA16 = 'f7d849e974904492'

A = sys.argv
MODE = 'base'
for m in ('--probe', '--fix', '--fix2', '--fix4'):
    if m in A:
        MODE = m.lstrip('-')
OUT = A[A.index('--out') + 1] if '--out' in A else 'D:/Temp/r83/work/out_%s.py' % MODE
SRC = A[A.index('--src') + 1] if '--src' in A else None


def sha16(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]


# ── anchor: the chain-result assembly line inside `_check_elif_chain` ──────────────
ANCHOR = "            result = {'conditions': conditions, 'bodies': bodies, 'final_else': final_else}"

HELPER = '''            # [R21-53 普查探针] 只记录，不判定、不改变任何返回值。判据主体不使用其读数。
            _r2153_census('EVAL', {
                'header': getattr(header_, 'start_offset', None),
                'conds': [getattr(c, 'start_offset', None) for c in conditions],
                'final_else_n': len(final_else),
                'final_else_head': [getattr(b, 'start_offset', None) for b in final_else[:3]],
                'fe': _r2153_sig(header_, conditions, final_else, self),
            })
'''

FIX = '''            # [R21-53 判据] 仅剔除「假出口落在父臂体内」的那一条 elif 条件（及其配对臂），
            # 整条链的 final_else（链尾归属）一字不动。取材面：候选 elif 条件块的终结条件
            # 跳转落点（CFG 后继结构）+ 已声明 IfRegion 的 then_blocks 成员资格 + 本链自身
            # final_else 成员资格；不读函数名、绝对偏移、计数器、跨层次回补。
            _r2153_drop = _r2153_refuse_indices(conditions, final_else)
            if _r2153_drop:
                _r2153_census('FIRE', {
                    'header': getattr(header_, 'start_offset', None),
                    'dropped': [getattr(conditions[i], 'start_offset', None) for i in _r2153_drop],
                    'final_else_n_before': len(final_else),
                })
                conditions = [c for _i, c in enumerate(conditions) if _i not in _r2153_drop]
                bodies = [b for _i, b in enumerate(bodies) if _i not in _r2153_drop]
                _r2153_census('FIRE_AFTER', {'final_else_n': len(final_else),
                                             'conds_n': len(conditions)})
                if not conditions:
                    return None
'''

FIX2 = '''            # [R21-53·V2 判据] 同一签名，但**不放弃链**：把被降格的那条 elif 臂整体并入
            # 本链自己的 final_else —— 链尾归属只增不减（[R21-49] 的 -269 正是归属缩水）。
            _r2153_drop = _r2153_refuse_indices(conditions, final_else)
            if _r2153_drop:
                _r2153_census('FIRE', {
                    'header': getattr(header_, 'start_offset', None),
                    'dropped': [getattr(conditions[i], 'start_offset', None) for i in _r2153_drop],
                    'final_else_n_before': len(final_else),
                })
                _r2153_demoted = []
                for _i in sorted(_r2153_drop):
                    _r2153_demoted.append(conditions[_i])
                    _r2153_demoted.extend(bodies[_i] if _i < len(bodies) else [])
                conditions = [c for _i, c in enumerate(conditions) if _i not in _r2153_drop]
                bodies = [b for _i, b in enumerate(bodies) if _i not in _r2153_drop]
                final_else = _r2153_demoted + list(final_else)
                _r2153_census('FIRE_AFTER', {'final_else_n': len(final_else),
                                             'conds_n': len(conditions)})
'''

FIX4 = """            # [R21-53·V4 判据] 同一签名；降格时只把该臂的**入口块**并入本链 final_else，
            # 臂的内部块（其自身 IfRegion 已经在渲染它们）不重复登记，避免平坦语句表在
            # 「已渲染过的子区域块」处中止（V2 实测因此丢掉链尾 269 条指令）。
            _r2153_drop = _r2153_refuse_indices(conditions, final_else)
            if _r2153_drop:
                _r2153_census('FIRE', {
                    'header': getattr(header_, 'start_offset', None),
                    'dropped': [getattr(conditions[i], 'start_offset', None) for i in _r2153_drop],
                    'final_else_n_before': len(final_else),
                })
                _r2153_entries = [conditions[_i] for _i in sorted(_r2153_drop)]
                conditions = [c for _i, c in enumerate(conditions) if _i not in _r2153_drop]
                bodies = [b for _i, b in enumerate(bodies) if _i not in _r2153_drop]
                final_else = _r2153_entries + list(final_else)
                _r2153_census('FIRE_AFTER', {'final_else_n': len(final_else),
                                             'conds_n': len(conditions)})
"""

PROBE_FN = '''def _r2153_census(stage, detail=''):
    """[R21-53 普查探针] 仅当环境变量 R2153_CENSUS 指向路径时追加一行；否则立即返回。

    探针不参与任何判定：判据主体不使用它的返回值。开/关探针必须产物逐字节一致，否则
    普查读数作废（规则 2）。
    """
    import os as _os_r2153
    _p = _os_r2153.environ.get('R2153_CENSUS')
    if not _p:
        return
    try:
        with open(_p, 'a', encoding='utf-8') as _f_r2153:
            _f_r2153.write('%s %s' % (stage, detail) + chr(13) + chr(10))
    except Exception:
        pass


def _r2153_false_exit(cond):
    """[R21-53] 候选 elif 条件块的假出口：末条前向条件跳转 IF_FALSE 的目标块。

    只读该块自身的终结子（原则 1：块 = 前导语句 + 恰好一个终结子）。返回 None 表示
    该块没有可辨识的假出口（不是前向 IF_FALSE 结尾），判据对此保持沉默。
    """
    _last = cond.get_last_instruction()
    if _last is None or _last.argval is None:
        return None
    _op = _last.opname
    if _op not in FORWARD_CONDITIONAL_JUMP_OPS:
        return None
    if 'IF_FALSE' not in _op:
        return None
    for _s in (cond.successors or ()):
        if getattr(_s, 'start_offset', None) == _last.argval:
            return _s
    return None


def _r2153_sig(header_, conditions, final_else, self=None):
    """[R21-53 共享出口签名] 每条候选 elif 条件的合取读数。

    返回 [(index, false_exit_offset, in_other_then_blocks, in_final_else)]；
    证据不足（无假出口）的条件不出现。
    """
    _out = []
    if self is None:
        return _out
    _fset = set(final_else or [])
    for _i, _c in enumerate(conditions):
        _fe = _r2153_false_exit(_c)
        if _fe is None:
            continue
        _in_then = False
        for _r in list(getattr(self, '_current_if_regions', None) or []) + \\
                 list(getattr(self, 'regions', None) or []):
            if not isinstance(_r, IfRegion):
                continue
            if _r.condition_block is _c:
                continue
            if _fe in (_r.then_blocks or []):
                _in_then = True
                break
        _out.append((_i, getattr(_fe, 'start_offset', None), _in_then, _fe in _fset))
    return _out
'''

REFUSE_FN = '''def _r2153_refuse_indices_impl(self, conditions, final_else):
    """[R21-53] 合取：候选 elif 条件的假出口 F 同时是
       ① 某个已声明 IfRegion 的 then_blocks 成员（父臂把自己声明为该体的语句序列），且
       ② 本链自身 final_else 的成员（本链又把它当链尾 else 体）。
       真 elif 条件的假出口只会是下一条腿或链尾，不会落进父臂声明的体内；一条腿的假出口
       同时被父臂与本链两头声明，说明这条腿不是 elif，而是父臂里的一条独立语句。
       证据不足一律返回空集（保守：维持既有收集）。
    """
    _drop = set()
    _fset = set(final_else or [])
    if not _fset:
        return _drop
    for _i, _c in enumerate(conditions):
        _fe = _r2153_false_exit(_c)
        if _fe is None or _fe not in _fset:
            continue
        _in_other_then = False
        for _r in list(getattr(self, '_current_if_regions', None) or []) + \\
                 list(getattr(self, 'regions', None) or []):
            if not isinstance(_r, IfRegion):
                continue
            if _r.condition_block is _c:
                continue
            if _fe in (_r.then_blocks or []):
                _in_other_then = True
                break
        if _in_other_then:
            _drop.add(_i)
    return _drop
'''

# ── build ────────────────────────────────────────────────────────────────────────

src_path = SRC or os.path.join(REPO, 'core/cfg/region_analyzer.py')
raw = open(src_path, 'rb').read()
if MODE == 'base':
    assert sha16(raw) == ANALYZER_LANDED_SHA16, (sha16(raw), ANALYZER_LANDED_SHA16)
    open(OUT, 'wb').write(raw)
    print('[base-copy] %s -> %s sha16=%s (unchanged)' % (src_path, OUT, sha16(raw)))
    sys.exit(0)

assert b'\r\r\n' not in raw, 'source already has CR CR LF'
lines = raw.split(b'\r\n')
n_before = len(lines)
hits = [i for i, l in enumerate(lines) if l.decode('utf-8', 'replace') == ANCHOR]
assert len(hits) == 1, 'anchor not unique: %d hits' % len(hits)
idx = hits[0]

# module-level helper functions: append right before the class body? they are used as
# free functions + a bound method; place them at module scope by inserting after the
# constant tables (they reference FORWARD_CONDITIONAL_JUMP_OPS / IfRegion).
HELPER_FN = (PROBE_FN if MODE == 'probe' else PROBE_FN + '\n' + REFUSE_FN).replace('\n', '\r\n')

ins = []
ins += [ln.encode('utf-8') for ln in HELPER_FN.split('\r\n') if ln != '']
# probe/fix call site inside the closure
VMAP = {'fix': FIX, 'fix2': FIX2, 'fix4': FIX4}
PATCH_TXT = HELPER if MODE == 'probe' else (HELPER + VMAP[MODE])
call_lines = PATCH_TXT
ins_at_anchor = [ln.encode('utf-8') for ln in call_lines.replace('\n', '\r\n').split('\r\n') if ln != '']

# bind self into the helpers: the closure has `self`; wire the signature helper through a
# module-level function object assigned to the analyzer as a private method.
REFUSE_BIND = b"            _r2153_refuse_indices = lambda _cs, _fe: _r2153_refuse_indices_impl(self, _cs, _fe)"

new_lines = lines[:idx] + [REFUSE_BIND] + ins_at_anchor + [lines[idx]] + lines[idx + 1:]
out = b'\r\n'.join(new_lines)

# module-level helper insertion point: right after the SHORT_CIRCUIT_JUMP_OPS table block
marker = b'SHORT_CIRCUIT_JUMP_OPS = frozenset({'
mpos = out.find(marker)
assert mpos != -1
# find the end of that frozenset literal (first "})" after marker)
end = out.find(b'})', mpos) + 2
helper_bytes = b'\r\n\r\n' + b'\r\n'.join([ln.encode('utf-8') for ln in HELPER_FN.split('\r\n') if ln != ''])
out = out[:end] + helper_bytes + out[end:]

assert sha16(out) != sha16(raw)
open(OUT, 'wb').write(out)
py_compile.compile(OUT, doraise=True)
back = open(OUT, 'rb').read()
assert b'\r\r\n' not in back, 'CR CR LF introduced'
assert back.startswith(b'\xef\xbb\xbf'), 'BOM lost'
print('[%s] src sha16=%s  out sha16=%s  lines %d -> %d  bytes %d -> %d' % (
    MODE, sha16(raw), sha16(back), n_before, len(back.split(b'\r\n')), len(raw), len(back)))
print('OUT=%s' % OUT)
