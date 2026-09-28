# -*- coding: utf-8 -*-
"""Round 74 post-landing pipeline (run detached AFTER land74 --apply).
Each step skips itself when its declared outputs already exist (resume-safe).
Appends to dump/_driver74b.log; failures abort with an ABORT marker.
"""
import json
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')
C = os.path.dirname(os.path.abspath(__file__))
REPO = r'F:/Downloads/pythoncdc-main'
LOG = os.path.join(C, 'dump', '_driver74b.log')
D = os.path.join(C, 'dump')


def io_open(p, m):
    return open(p, m, encoding='utf-8', errors='replace')


def log(msg):
    with io_open(LOG, 'a') as f:
        f.write(msg + '\n')


def have(*paths):
    return all(os.path.isfile(os.path.join(C, p)) for p in paths)


def run(args, cwd=C, out=None, tag=''):
    log('CMD %s%s' % (' '.join(args), ('  cwd=' + cwd) if cwd != C else ''))
    p = subprocess.run([sys.executable, '-W', 'ignore', '-X', 'utf8'] + args,
                       cwd=cwd, capture_output=True, text=True, encoding='utf-8',
                       errors='replace')
    if out:
        with io_open(out, 'w') as f:
            f.write((p.stdout or '') + (p.stderr or ''))
    else:
        log((p.stdout or '')[-1500:] + (p.stderr or '')[-800:])
    log('  rc=%d %s' % (p.returncode, tag))
    if p.returncode != 0:
        log('ABORT %s' % tag)
    return p.returncode


def step(tag, outs, args, cwd=C, out=None):
    if have(*outs):
        log('SKIP %s (outputs present)' % tag)
        return 0
    return run(args, cwd=cwd, out=out, tag=tag)


def main():
    with io_open(LOG, 'w') as f:
        f.write('driver74b start\n')

    # 0. prev mirror (HEAD blobs)
    if not os.path.isdir(os.path.join(C, 'mirr_prev')):
        if run(['mkmirr_prev74.py'], tag='mkmirr_prev') != 0:
            return 1
    else:
        log('SKIP mkmirr_prev')
    # 1-5. measurements
    if step('repro65_prev', ('dump/repro65_prev.jsonl',),
            ['h62.py', 'run', '--arm=prev', '--list=dump/reprolist65.txt',
             '--out=dump/repro65_prev.jsonl']) != 0:
        return 1
    if step('G3_batch', ('dump/G3_batch_r74.txt',),
            ['scripts/pyc_batch_verify.py', 'batch', '--index',
             os.path.join(REPO, 'pyc_index.json'), '--round', '74', '--all'],
            cwd=REPO, out=os.path.join(D, 'G3_batch_r74.txt')) != 0:
        return 1
    if step('landed_c2', ('dump/landed_c2.jsonl',),
            ['h62.py', 'run', '--arm=landed', '--list=dump/g1list.txt',
             '--out=dump/landed_c2.jsonl']) != 0:
        return 1
    if step('repro65_landed', ('dump/repro65_landed.jsonl',),
            ['h62.py', 'run', '--arm=landed', '--list=dump/reprolist65.txt',
             '--out=dump/repro65_landed.jsonl']) != 0:
        return 1
    if step('strict_landed', ('dump/strict_landed73.json',),
            ['sstrict67.py', 'build_landed', 'dump/g1list.txt',
             'dump/strict_landed73.json']) != 0:
        return 1
    # 6. G3v mandated shards (8 index shards)
    if not have('chunks/rep7.json'):
        ix = json.load(io_open(os.path.join(REPO, 'pyc_index.json'), 'r'))
        ents = ix['entries'] if isinstance(ix, dict) and 'entries' in ix else ix
        os.makedirs(os.path.join(C, 'chunks'), exist_ok=True)
        n = (len(ents) + 7) // 8
        for i in range(8):
            with io_open(os.path.join(C, 'chunks', 'ix%d.json' % i), 'w') as f:
                json.dump(ents[i * n:(i + 1) * n], f, ensure_ascii=False, indent=1)
        for i in range(8):
            if run(['scripts/pyc_verify.py', 'batch',
                    '--index', os.path.join(C, 'chunks', 'ix%d.json' % i),
                    '--json', os.path.join(C, 'chunks', 'rep%d.json' % i)],
                   cwd=REPO, tag='G3v shard %d' % i) != 0:
                return 1
    else:
        log('SKIP G3v shards')
    if step('merge_g3v', ('logs/G3v_pycverify_r74.json',), ['merge_g3v74.py']) != 0:
        return 1
    # 7. battery prev vs landed
    if step('battery', ('dump/batt_prev_landed74.txt',),
            ['closeout69.py', 'battery', 'prev', 'landed'],
            out=os.path.join(D, 'batt_prev_landed74.txt')) != 0:
        return 1
    # 8. G9 synth
    if step('g9', ('logs/G9_synth_r74.txt',), ['g9run74.py']) != 0:
        return 1
    # 9. gates
    if run(['gates74.py'], tag='gates74') != 0:
        return 1
    # 10. G4 / replay / G8
    if run(['g4g8replay74.py'], tag='g4g8replay') != 0:
        return 1
    # 11. try verdict summary
    if run(['tryverdict_summary74.py'], tag='tryverdict') != 0:
        return 1
    log('driver74b DONE')
    return 0


if __name__ == '__main__':
    sys.exit(main())
