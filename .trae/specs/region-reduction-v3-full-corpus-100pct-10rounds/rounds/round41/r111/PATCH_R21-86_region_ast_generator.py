# -*- coding: utf-8 -*-
"""PATCH_R21-86_region_ast_generator.py -- idempotent anchored patch, landed 566ff5c5 -> R21-86.

Rule [R21-86] "a branch may claim only the blocks it renders":
  (A) in _if_generate_normal's [R23] short-circuit-or branch, when the else arm is rendered from a
      elif chain BORROWED from a descendant region, the trailing claim of `region.else_blocks`
      marks only members inside that rendered chain's block scope; every other member is left
      unclaimed and recorded as released, so the owning parent sequence emits it exactly once;
  (B) the dispatch-adjacent blanket claim of `_nr.blocks` in _process_if_blocks honours that
      release instead of re-marking it.
Release is additionally gated on a structural safety relation: the released block must still be an
arm member of some region on the in-flight generation stack (an ancestor sequence that has not
finished walking), so nothing can be dropped.  Criteria read only region/block membership and the
in-flight stack -- no function names, no file names, no absolute offsets, no counters.

Absolute paths only.  Source is UTF-8 BOM + all-CRLF; asserts are re-run after writing.
usage: python -X utf8 PATCH_R21-86_region_ast_generator.py [--check]
"""
import hashlib
import io
import os
import sys

SRC = r'D:/Temp/r111/backup/gen_566ff5c502276e48.py'
OUT = r'D:/Temp/r111/cand_r2186_gen.py'
LAND_SHA = '566ff5c502276e48'

HELPER = '''def _r2186_rendered_else_scope(region):
    """[R21-86] The block scope of the else arm that `_if_generate_elif_chain` renders for
    `region`: the elif tests, the elif bodies and the chain-tail else list.

    When an if-region's else arm is produced by an elif chain, that chain's member lists ARE the
    rendered arm -- nothing outside them is printed by this branch.  Membership only; no offsets,
    no names, no instruction facts.
    """
    _scope = set()
    for _c in (getattr(region, 'elif_conditions', None) or ()):
        _scope.add(_c)
    for _body in (getattr(region, 'elif_bodies', None) or ()):
        if isinstance(_body, (list, tuple, set)):
            _scope.update(_body)
        else:
            _scope.add(_body)
    for _b in (getattr(region, 'elif_final_else', None) or ()):
        _scope.add(_b)
    return _scope


def _r2186_has_inflight_owner(gen, region, block):
    """[R21-86] True when some region OTHER than `region` that is currently on the generation
    stack (an ancestor sequence whose block walk has not returned yet) still lists `block` as one
    of its own arm members.

    Releasing a block from a claim is only safe while an owning sequence can still reach it: the
    ancestor walks iterate their arm lists and will emit the block there, exactly once.  Reads
    arm membership plus `_generating_regions` (the in-flight stack) -- a pure structural relation,
    not a jump target, offset, counter or name.
    """
    for _r in (gen.region_analyzer.regions or ()):
        if _r is region or id(_r) not in gen._generating_regions:
            continue
        if block in (getattr(_r, 'then_blocks', None) or ()):
            return True
        if block in (getattr(_r, 'else_blocks', None) or ()):
            return True
    return False


'''

SITE_A_OLD = '''            if _or_elif_ir is not None:
                # [关键修复] 临时将 _or_then_block 添加到 then_blocks，
                # 否则 _process_if_blocks 会因 block 有 RETURN_VALUE 且不在 then_blocks 中而跳过它
                _saved_then_blocks = region.then_blocks
                if _r23_or_then and _r23_or_then not in region.then_blocks:
                    region.then_blocks = list(region.then_blocks) + [_r23_or_then]
                then_stmts = self._process_if_blocks([_r23_or_then], region, branch='then')
                region.then_blocks = _saved_then_blocks
                if not hasattr(region, 'elif_conditions') or not region.elif_conditions:
                    region.elif_conditions = _or_elif_ir.elif_conditions
                    region.elif_bodies = _or_elif_ir.elif_bodies
                    region.elif_final_else = getattr(_or_elif_ir, 'elif_final_else', None)
                else_stmts = self._if_generate_elif_chain(region)'''

SITE_A_NEW = '''            if _or_elif_ir is not None:
                # [关键修复] 临时将 _or_then_block 添加到 then_blocks，
                # 否则 _process_if_blocks 会因 block 有 RETURN_VALUE 且不在 then_blocks 中而跳过它
                _saved_then_blocks = region.then_blocks
                if _r23_or_then and _r23_or_then not in region.then_blocks:
                    region.then_blocks = list(region.then_blocks) + [_r23_or_then]
                then_stmts = self._process_if_blocks([_r23_or_then], region, branch='then')
                region.then_blocks = _saved_then_blocks
                _r2186_chain_borrowed = False
                if not hasattr(region, 'elif_conditions') or not region.elif_conditions:
                    region.elif_conditions = _or_elif_ir.elif_conditions
                    region.elif_bodies = _or_elif_ir.elif_bodies
                    region.elif_final_else = getattr(_or_elif_ir, 'elif_final_else', None)
                    _r2186_chain_borrowed = True
                else_stmts = self._if_generate_elif_chain(region)'''

SITE_A_CLAIM_OLD = '''                for b in region.else_blocks:
                    if b is not _r23_or_then and b is not _r23_or_else and b is not _r23_or_rhs:
                        if b not in self.generated_blocks:
                            self.generated_blocks.add(b)
            else:'''

SITE_A_CLAIM_NEW = '''                # [R21-86 RENDER-SCOPED CLAIM] 本分支的 else 臂由 `_if_generate_elif_chain` 从
                # *借来* 的后代 elif 链渲染；链的成员表就是被打印的臂，`else_blocks` 中不在该
                # 臂内的块本分支一个也没输出。原则 2（每块唯一归属且归属者必须发射）要求这里
                # 不得认领自己并未渲染的块：把它们留给真正遍历到它们的那条父序列发射一次。
                # 认领条件（全部是本分支自己的结构事实，判定即在此处完成，不回读已生成的文本）：
                #   ① 只有当 else 臂确实是借来的链时（本区原先没有 elif 链）才收窄；
                #   ② 块必须落在该链的渲染范围（elif_conditions / elif_bodies / elif_final_else）
                #      内，否则只有在某条仍在生成栈上的祖先序列把它列为自己的臂成员时才释放，
                #      保证释放出去的块一定还会被发射一次（不会丢码）。
                _r2186_scope = (_r2186_rendered_else_scope(region)
                                if _r2186_chain_borrowed else None)
                for b in region.else_blocks:
                    if b is not _r23_or_then and b is not _r23_or_else and b is not _r23_or_rhs:
                        if b not in self.generated_blocks:
                            if _r2186_scope is None or b in _r2186_scope:
                                self.generated_blocks.add(b)
                            elif _r2186_has_inflight_owner(self, region, b):
                                self._r2186_released_blocks.add(b)
                            else:
                                self.generated_blocks.add(b)
            else:'''

SITE_B_OLD = '''                for _nb in _nr.blocks:
                    if (not _nr_ast and _nb is not _nr.entry and _nb in child_entries):
                        continue
                    self.generated_blocks.add(_nb)'''

SITE_B_NEW = '''                # [R21-86] 子区域的臂渲染器把自己没有渲染的 else_blocks 成员显式释放给了调用它的
                # 序列（见 _if_generate_normal 的 RENDER-SCOPED CLAIM）。本行的全集认领若把它们
                # 重新标记，父序列就永远走不到它们；其余块照旧认领，避免重复发射。
                for _nb in _nr.blocks:
                    if (not _nr_ast and _nb is not _nr.entry and _nb in child_entries):
                        continue
                    if _nb in self._r2186_released_blocks:
                        continue
                    self.generated_blocks.add(_nb)'''

INIT_OLD = '        self.generated_blocks: Set[BasicBlock] = set()'
INIT_NEW = ('        self.generated_blocks: Set[BasicBlock] = set()\n'
            '        # [R21-86] blocks an arm renderer released to its owning parent sequence\n'
            '        self._r2186_released_blocks: Set[BasicBlock] = set()')

ANCHOR = 'def _r2114_defer_to_unemitted_sibling_loop(gen, block, child):'

EDITS = [
    ('init ledger', INIT_OLD, INIT_NEW, '\r\n'),
    ('helper', ANCHOR, HELPER + ANCHOR, '\r\n'),
    ('site A graft flag', SITE_A_OLD, SITE_A_NEW, '\r\n'),
    ('site A claim', SITE_A_CLAIM_OLD, SITE_A_CLAIM_NEW, '\r\n'),
    ('site B claim', SITE_B_OLD, SITE_B_NEW, '\r\n'),
]


def main():
    raw = open(SRC, 'rb').read()
    assert raw[:3] == b'\xef\xbb\xbf', 'source lacks BOM'
    assert hashlib.sha256(raw).hexdigest()[:16] == LAND_SHA, 'source is not the landed generator'
    text = raw.decode('utf-8-sig')
    lines = text.split('\r\n')
    assert '\n' not in ''.join(lines[:1]), 'stray LF'
    out = '\r\n'.join(lines)
    for name, old, new, joiner in EDITS:
        old_n = old.replace('\n', joiner)
        new_n = new.replace('\n', joiner)
        cnt = out.count(old_n)
        assert cnt == 1, 'anchor %r found %d times' % (name, cnt)
        if new_n in out:
            print('  %-22s already applied' % name)
            continue
        out = out.replace(old_n, new_n, 1)
        print('  %-22s applied' % name)
    body = ('\ufeff' + out.replace('\ufeff', '')).encode('utf-8')
    open(OUT, 'wb').write(body)
    chk = open(OUT, 'rb').read()
    assert chk[:3] == b'\xef\xbb\xbf', 'BOM lost'
    assert chk.count(b'\r\r\n') == 0, 'CR CR LF introduced'
    bare = sum(1 for i, c in enumerate(chk) if c == 0x0A and (i == 0 or chk[i - 1] != 0x0D))
    assert bare == 0, 'bare LF introduced: %d' % bare
    compile(chk.decode('utf-8-sig'), OUT, 'exec')
    print('wrote %s size=%d sha16=%s py_compile=OK' % (
        OUT, len(chk), hashlib.sha256(chk).hexdigest()[:16]))
    if '--check' in sys.argv:
        io.open(os.devnull, 'w').write('')


main()
