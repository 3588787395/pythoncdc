"""hunk_attribution_r107.py — which ladder steps are still open, from the product text alone.

usage: python -X utf8 hunk_attribution_r107.py <product.py>

Prints the clock_worker body diff against the byte-identical 13/13 oracle, hunk by hunk, with a
step label derived from the keywords in each hunk's gold-side lines. `oracle_diff_r104.py` answers
"how far" (count + census + judge); this answers "of what". Hunk segmentation here is difflib's own
with n=2 context, so it can disagree with the rig's count — read the labels, not the number.
"""
import difflib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GOLD = os.path.join(HERE, 'GOLD_realtime_event_source_PROOF.py')

STEP_KEYS = [
    ('step4 is_holiday or-chains @6322/@6496', ('is_holiday_today', 'PRE_BEFORE_TRADING_START', 'BEFORE_TRADING_START')),
    ('step3 or-chain @7164 + swallowed debug', ('login_semaphore', '获取重登信号量')),
    ('step1 reconnect/persist tail @7972..@8586', ('broker_persist', 'jsonpickle', '获取持久化对象', 'server_restart_not_do_before')),
    ('step6 chained-compare fold @8904/@8948', ('pre_trade_time', 'post_trade_time', 'initial_trading_date')),
    ('step5 while-True wrapper', ('while True',)),
    ('step2 spurious wrapper body', ('event_queue.put', 'SYSTEM_REBUILD')),
]


def body(path):
    src = open(path, encoding='utf-8-sig', errors='replace').read().replace('\r\n', '\n').split('\n')
    out, started, ind = [], False, None
    for line in src:
        if not started and re.match(r'\s*def clock_worker\(', line):
            started, ind = True, len(line) - len(line.lstrip())
            out.append(line)
            continue
        if started:
            if line.strip():
                cur = len(line) - len(line.lstrip())
                if cur <= ind and not line.strip().startswith(('@', '#')):
                    break
            out.append(line)
    return out


def classify(gold_lines):
    blob = '\n'.join(gold_lines)
    labels = [name for name, keys in STEP_KEYS if any(k in blob for k in keys)]
    return labels or ['unlabelled']


def main():
    prod = sys.argv[1]
    g, p = body(GOLD), body(prod)
    print('gold_lines=%d prod_lines=%d delta=%+d' % (len(g), len(p), len(p) - len(g)))
    d = list(difflib.unified_diff(g, p, 'GOLD', 'PROD', lineterm='', n=2))
    hunks, cur = [], None
    for line in d:
        if line.startswith('@@'):
            m = re.match(r'@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@', line)
            cur = {'hdr': line, 'gold': m.group(1), 'gn': m.group(2), 'del': [], 'ins': []}
            hunks.append(cur)
            continue
        if cur is None:
            continue
        if line.startswith('-'):
            cur['del'].append(line[1:])
        elif line.startswith('+'):
            cur['ins'].append(line[1:])
    print('hunks=%d' % len(hunks))
    for i, h in enumerate(hunks, 1):
        print('H%d %s  del=%d ins=%d  -> %s' % (
            i, h['hdr'], len(h['del']), len(h['ins']), ', '.join(classify(h['del'] + h['ins']))))
        for l in (h['del'] + h['ins'])[:6]:
            print('     %s' % l.strip()[:100])
    if not hunks:
        print('ZERO HUNKS: text parity with the oracle (sufficient-not-necessary for the judge).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
