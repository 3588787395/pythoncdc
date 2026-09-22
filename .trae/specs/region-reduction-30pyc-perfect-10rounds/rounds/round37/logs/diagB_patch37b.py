# -*- coding: utf-8 -*-
"""Round 37 diagB: apply the REFINED candidate R37-B' to the mirror copy of the core.

  python -X utf8 patch37b.py

R37-B' (same-layer, ownership-only):
  An if-arm must end before its own **pure transfer block**: a collected arm block T whose
  non-noise instructions are nothing but an unconditional jump, when T's jump target has a
  normal predecessor outside {the arm, this if's condition/chain blocks, the two arm entries,
  merge}.  Such a T carries no statement (principle 1) and its target is a convergence point
  of an enclosing region, so T belongs to the ancestor's terminal, not to this arm
  (principle 2).  Everything from T on is therefore the ancestor's continuation.
"""
import os
import shutil
import sys

REPO = r'F:\Downloads\pythoncdc-main'
SCRATCH = r'D:/Temp/r37diagB'
MIRROR = os.path.join(SCRATCH, 'mirr_probe')
RA = os.path.join(MIRROR, 'core', 'cfg', 'region_analyzer.py')
TRACE = os.path.join(SCRATCH, 'out', 'r37b_trace.txt')

JUMPS = ('JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE', 'JUMP_NOARGS', 'JUMP')

SRC_METHOD = '''    def _r37_arm_collect(self, arm_entry, merge, stop_set, arm_name='', exempt=None):
        """[R37-B' candidate] if-arm bounded by its own pure transfer block.

        Truncates the arm collected by _collect_branch_blocks before the first arm block T
        that (a) holds no statement at all -- after dropping NOISE ops its instruction list
        is a single unconditional jump -- and (b) jumps to a block that has a normal
        predecessor outside the arm (excluding this if's own condition / chain blocks, the
        two arm entries and merge).  T is then the *enclosing* region's terminal transfer,
        not content of this arm, and the target is an ancestor convergence block: by
        principle 2 (one owner per block) the arm stops before T.
        """
        collected = self._collect_branch_blocks(arm_entry, merge, stop_set)
        _ex = set(exempt or ())
        _ex.update([b for b in (arm_entry, merge) if b is not None])
        _noise = ('NOP', 'CACHE', 'PRECALL', 'EXTENDED_ARG')
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
            _ops = [i.opname for i in _b.instructions if i.opname not in _noise]
            if len(_ops) != 1 or not _ops[0].startswith('JUMP'):
                continue
            _succ = set(_b.successors) - set(getattr(_b, 'exception_successors', None) or ())
            if len(_succ) != 1:
                continue
            _j = next(iter(_succ))
            _outside = set(_j.predecessors) - _seen - _ex
            if _outside:
                if _tr:
                    open(r'%s', 'a', encoding='utf-8').write(
                        'TRUNC arm=%%s at=%%s target=%%s dropped=%%s outside_preds=%%s kept=%%s\\n' %% (
                            arm_name, _b.start_offset, _j.start_offset,
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


def main():
    shutil.rmtree(MIRROR)
    os.makedirs(MIRROR)
    shutil.copytree(os.path.join(REPO, 'core'), os.path.join(MIRROR, 'core'),
                    ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copyfile(os.path.join(REPO, 'pycdc.py'), os.path.join(MIRROR, 'pycdc.py'))
    txt = open(RA, encoding='utf-8').read()
    for old, new in ((CALL_THEN_OLD, CALL_THEN_NEW), (CALL_ELSE_OLD, CALL_ELSE_NEW),
                     (BUILD_OLD, SRC_METHOD + BUILD_OLD)):
        assert txt.count(old) == 1, 'anchor count %d for %r' % (txt.count(old), old[:40])
        txt = txt.replace(old, new)
    with open(RA, 'w', encoding='utf-8', newline='\n') as f:
        f.write(txt)
    print('R37-B-prime patched ->', RA)


if __name__ == '__main__':
    main()
