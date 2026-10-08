# -*- coding: utf-8 -*-
"""Round-10 gate-tooling guards (static, no `core` import, no emitter run).

Two defects found while pre-flighting the round-10 gate were silent: a ledger tool could measure a
different checkout than the running worktree, and the gate driver could lose a truncated shard
forever. Both are re-checkable by reading the tool text, so they live here as resident teeth
instead of one-time readings.
"""
import io
import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SPEC = os.path.join(ROOT, '.trae', 'specs', 'region-reduction-v3-full-corpus-100pct-10rounds')
TOOL_GLOBS = [os.path.join('tools', 'kb'), SPEC]
REPO_NAME = 'pythoncdc-main'


def _tool_files():
    for base in TOOL_GLOBS:
        if not os.path.isdir(base):
            continue
        for name in sorted(os.listdir(base)):
            if name.endswith('.py'):
                yield os.path.join(base, name)


class TestNoHardcodedRepoRoot(unittest.TestCase):
    """A tool must derive its root from its own file, not name a checkout literally.

    The original hazard: `ROOT = Path(r"F:\\Downloads\\pythoncdc-main")` in a worktree. That path
    really existed on the machine, so the tool measured another checkout's source and wrote its
    JSON outside the worktree; the staleness checker compared this worktree's source against the
    other checkout's wiki pages and understated the residual (10 instead of 41).
    """

    def test_no_literal_repo_path(self):
        hits = []
        pat = re.compile(r'["\'][^"\']*%s[^"\']*["\']' % re.escape(REPO_NAME))
        for path in _tool_files():
            text = io.open(path, encoding='utf-8-sig').read()
            for num, line in enumerate(text.splitlines(), 1):
                if line.lstrip().startswith('#'):
                    continue
                if pat.search(line):
                    hits.append('%s:%d %s' % (os.path.relpath(path, ROOT), num, line.strip()))
        self.assertEqual([], hits, '工具写死了某个 checkout 的绝对路径（应改为按 __file__ 推导 ROOT）')


class TestGateDriverResume(unittest.TestCase):
    """`regen_list.py` exits rc=3 with `BUDGET NEXT=<cursor>`; the driver must feed it back.

    Without that, re-invoking the regen stage restarts every shard at zero, so a truncated shard
    is never caught up and `verify` would compare a half-regenerated corpus — which reads green
    under a compare-only judge.
    """

    def setUp(self):
        src = io.open(os.path.join(SPEC, 'gate_round.py'), encoding='utf-8-sig').read()
        self.body = src.split('def stage_regen')[1].split('def stage_verify')[0]

    def test_passes_start_cursor_back(self):
        # measured against the pre-fix blob (git show HEAD~1 of the driver): 'NEXT=' and 'rc == 3'
        # are both already present there (the old code only *printed* the resume point), so an
        # assertion on them reads green on the broken text and is decoration. The two assertions
        # that actually bite are the start argument and the per-shard resume loop.
        self.assertIn('str(cursor)', self.body, 'regen 段不再把游标作为 start 传回产码器')

    def test_every_shard_is_driven_to_completion(self):
        self.assertIn('while True', self.body,
                      'regen 段每片只跑一次即视为完成：预算截断后该片永不补齐')


if __name__ == '__main__':
    unittest.main()
