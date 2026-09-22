# -*- coding: utf-8 -*-
"""Round 37 diagB: apply candidate R37-B to the MIRROR copy of the core (never the worktree).

  python -X utf8 patch37.py          -> patch mirr_probe/core/cfg/region_analyzer.py
  python -X utf8 patch37.py --revert -> re-copy the pristine mirror

R37-B (same-layer, structural only):
  An if-arm collected by _collect_branch_blocks must stop before the first arm block that
  has a normal predecessor OUTSIDE {arm blocks, this if's own condition/chain blocks, the two
  arm entries, merge}: such a block is a convergence point owned by the enclosing sequence
  (principle 2 = one owner per block, principle 1 = block = statements + terminating jump),
  not the descendant arm's body.
Nothing in F:/Downloads/pythoncdc-main is written by this script.
"""
import os
import shutil
import sys

REPO = r'F:\Downloads\pythoncdc-main'
SCRATCH = r'D:/Temp/r37diagB'
MIRROR = os.path.join(SCRATCH, 'mirr_probe')
RA = os.path.join(MIRROR, 'core', 'cfg', 'region_analyzer.py')
TRACE = os.path.join(SCRATCH, 'out', 'r37_trace.txt')

SRC_METHOD = '''    def _r37_arm_collect(self, arm_entry, merge, stop_set, arm_name='', exempt=None):
        """[R37-B candidate probe] bounded if-arm collection.

        Wraps _collect_branch_blocks and truncates the collected arm before the first
        arm block that has a normal predecessor outside the arm itself (excluding this
        if's own condition / chain blocks and the two arm entries).  Such a block is an
        ancestor-level convergence point (principle 2: one owner per block), so the
        descendant arm must not claim it or anything behind it.
        """
        collected = self._collect_branch_blocks(arm_entry, merge, stop_set)
        _ex = set(exempt or ())
        _ex.update([b for b in (arm_entry, merge) if b is not None])
        _tr = bool(__import__('os').environ.get('R37TRACE'))
        if _tr:
            open(r'%s', 'a', encoding='utf-8').write(
                'ENTER arm=%%s entry=%%s merge=%%s n=%%s exempt=%%s\\n' %% (
                    arm_name, getattr(arm_entry, 'start_offset', None),
                    getattr(merge, 'start_offset', None), len(collected),
                    sorted(getattr(b, 'start_offset', -1) for b in _ex)))
        if len(collected) <= 1:
            return collected
        _seen = set(collected)
        for _i, _b in enumerate(collected):
            if _i == 0:
                continue
            _outside = (set(_b.predecessors) | set()) - _seen - _ex
            if _outside:
                if _tr:
                    open(r'%s', 'a', encoding='utf-8').write(
                        'TRUNC arm=%%s at=%%s dropped=%%s outside_preds=%%s kept=%%s\\n' %% (
                            arm_name, _b.start_offset,
                            [x.start_offset for x in collected[_i:]],
                            sorted(x.start_offset for x in _outside),
                            [x.start_offset for x in collected[:_i]]))
                return collected[:_i]
        return collected

''' % (TRACE, TRACE)

CALL_THEN_OLD = """            then_blocks = self._collect_branch_blocks(then_succ, merge, then_stop)
            # 区域归约算法原则 2（每块唯一归属）+ 原则 4（入口引用语义）："""
CALL_THEN_NEW = """            then_blocks = self._r37_arm_collect(
                then_succ, merge, then_stop, 'then',
                exempt={block, then_succ, else_succ, merge} | set(chain_blocks or ()))
            # 区域归约算法原则 2（每块唯一归属）+ 原则 4（入口引用语义）："""

CALL_ELSE_OLD = """            else_blocks = self._collect_branch_blocks(else_succ, merge, else_stop)
            # 区域归约算法：try/with handler 块过滤"""
CALL_ELSE_NEW = """            else_blocks = self._r37_arm_collect(
                else_succ, merge, else_stop, 'else',
                exempt={block, then_succ, else_succ, merge} | set(chain_blocks or ()))
            # 区域归约算法：try/with handler 块过滤"""

BUILD_OLD = "    def _build_elif_region(self, block, then_blocks, else_blocks, merge, all_condition_blocks,"


def patch():
    txt = open(RA, encoding='utf-8').read()
    assert '_r37_arm_collect' not in txt, 'already patched'
    n = txt.count(CALL_THEN_OLD)
    assert n == 1, 'then anchor count %d' % n
    txt = txt.replace(CALL_THEN_OLD, CALL_THEN_NEW)
    n = txt.count(CALL_ELSE_OLD)
    assert n == 1, 'else anchor count %d' % n
    txt = txt.replace(CALL_ELSE_OLD, CALL_ELSE_NEW)
    n = txt.count(BUILD_OLD)
    assert n == 1, 'method anchor count %d' % n
    txt = txt.replace(BUILD_OLD, SRC_METHOD + BUILD_OLD)
    with open(RA, 'w', encoding='utf-8', newline='\n') as f:
        f.write(txt)
    for p in ('\\__pycache__',):
        pass
    pp = os.path.join(MIRROR, 'core', 'cfg', '__pycache__')
    if os.path.isdir(pp):
        shutil.rmtree(pp)
    print('patched OK ->', RA)
    for probe in (CALL_THEN_NEW.splitlines()[0], CALL_ELSE_NEW.splitlines()[0],
                  'def _r37_arm_collect'):
        print('  present:', probe.strip(), probe.strip() in open(RA, encoding='utf-8').read())


if '--revert' in sys.argv:
    shutil.rmtree(MIRROR)
    os.makedirs(MIRROR)
    shutil.copytree(os.path.join(REPO, 'core'), os.path.join(MIRROR, 'core'),
                    ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copyfile(os.path.join(REPO, 'pycdc.py'), os.path.join(MIRROR, 'pycdc.py'))
    print('mirror reverted to pristine bytes')
else:
    patch()
