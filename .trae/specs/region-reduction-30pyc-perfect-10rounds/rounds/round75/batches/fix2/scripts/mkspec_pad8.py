# -*- coding: utf-8 -*-
"""fix2: worktree-vs-HEAD diff -> specs/pad8_*.json (agent spec format).

一个 spec = {"file": "core/cfg/<x>.py", "edits": [{anchor, repl}, ...]}
anchor/repl 均为 LF 归一文本；顺序应用到 HEAD 正文必须精确还原 worktree 正文。
单 edit 臂 pad8_1..N（每条一个文件），合并臂 pad8m_a / pad8m_b（按文件合并）。
"""
import io
import json
import os
import subprocess
import sys
from difflib import SequenceMatcher

sys.stdout.reconfigure(encoding='utf-8')
REPO = r'F:\Downloads\pythoncdc-main'
OUT = r'D:/Temp/opencode/r75gate/fix2/specs'
FILES = ['core/cfg/region_analyzer.py', 'core/cfg/region_ast_generator.py']


def head_text(rel):
    raw = subprocess.check_output(['git', '-C', REPO, 'show', 'HEAD:' + rel])
    return raw.decode('utf-8-sig').replace('\r\n', '\n')


def work_text(rel):
    raw = io.open(os.path.join(REPO, rel.replace('/', os.sep)), 'rb').read()
    bom = raw[:3] == b'\xef\xbb\xbf'
    return raw.decode('utf-8-sig').replace('\r\n', '\n'), bom


def _grow(base, A, lo, hi, only_up=False):
    """把 [lo,hi) 窗口向上下扩，直到该段文本在 base 中唯一。insert 形态只许向上扩
    （保证 anchor 仍以插入点前一行为结尾，repl = anchor + 新行 = 在其后插入）。"""
    while True:
        if hi > lo:
            cand = '\n'.join(A[lo:hi])
            if cand.strip() and base.count(cand) == 1:
                return lo, hi
        if hi < len(A) and not only_up:
            hi += 1
            continue
        if lo > 0:
            lo -= 1
            continue
        if hi < len(A):
            hi += 1
            continue
        raise AssertionError('cannot make unique anchor at %d:%d' % (lo, hi))


def to_edits(base, new):
    """SequenceMatcher line opcodes -> [(anchor, repl)]，anchor 均取自 base 且唯一。"""
    A, B = base.split('\n'), new.split('\n')
    sm = SequenceMatcher(None, A, B, autojunk=False)
    raw = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            continue
        raw.append([tag, i1, i2, j1, j2])
    # 相邻/贴近 hunk 合并（间隔 <=1 行的两个 hunk 并成一个，anchor 取中间行）
    merged = []
    for h in raw:
        if merged and h[0] != 'delete' and merged[-1][0] != 'delete':
            p = merged[-1]
            if h[1] - p[2] <= 1:
                merged[-1] = ['replace', p[1], h[2], p[3], h[4]]
                continue
        merged.append(h)
    edits = []
    for tag, i1, i2, j1, j2 in merged:
        if tag == 'insert':
            assert i1 > 0, 'insert at file head unsupported'
            lo, hi = _grow(base, A, i1 - 1, i1, only_up=True)
            anchor = '\n'.join(A[lo:hi])
            repl = '\n'.join(A[lo:hi] + B[j1:j2])
        else:
            lo, hi = _grow(base, A, i1, i2)
            anchor = '\n'.join(A[lo:hi])
            jl = j1 - (i1 - lo)
            jr = j2 + (hi - i2)
            repl = '\n'.join(B[jl:jr])
        assert anchor.strip(), 'empty anchor at %d' % i1
        edits.append({'anchor': anchor, 'repl': repl})
    return edits


def apply(base, edits):
    t = base
    for k, e in enumerate(edits):
        n = t.count(e['anchor'])
        assert n == 1, 'anchor count=%d (edit %d): %r' % (n, k, e['anchor'][:70])
        t = t.replace(e['anchor'], e['repl'])
    return t


def write(name, rel, edits):
    p = os.path.join(OUT, name)
    io.open(p, 'w', encoding='utf-8', newline='\n').write(
        json.dumps({'file': rel, 'edits': edits}, ensure_ascii=False, indent=1))
    return p


def main():
    os.makedirs(OUT, exist_ok=True)
    per_file = {}
    n = 0
    for rel in FILES:
        base = head_text(rel)
        new, bom = work_text(rel)
        edits = to_edits(base, new)
        assert apply(base, edits) == new, 'round-trip failed for %s' % rel
        print('%s  bom=%s  edits=%d  lines %+d' %
              (rel, bom, len(edits), new.count('\n') - base.count('\n')))
        per_file[rel] = edits
        for e in edits:
            n += 1
            write('pad8_%d.json' % n, rel, [e])
            # 单 edit 臂自身也必须能从 HEAD 还原（等价于「只含此 edit」的正文）
            print('   pad8_%d  anchor=%d repl=%d' %
                  (n, e['anchor'].count('\n'), e['repl'].count('\n')))
    tag = 0
    for rel, eds in per_file.items():
        tag += 1
        write('pad8m_%s.json' % ('a' if tag == 1 else 'b'), rel, eds)
    print('single arms: pad8_1..pad8_%d ; merged: pad8m_a + pad8m_b' % n)


main()
