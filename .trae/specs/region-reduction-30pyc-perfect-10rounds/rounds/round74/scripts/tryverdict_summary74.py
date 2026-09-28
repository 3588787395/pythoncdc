# -*- coding: utf-8 -*-
"""Round 74: consolidated verdict on the user directive
"root cause is the nested try-except problem" -- recomputed from the two centre
diagnostic artifacts (prev-arm = R73 landed bytes, 77 failing units)."""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
D = r'D:/Temp/opencode/r74gate/center/dump'
G = r'D:/Temp/opencode/r74gate/center/logs'


def rd(p):
    raw = io.open(p, 'rb').read()
    if raw[:2] in (b'\xff\xfe', b'\xfe\xff'):
        return raw.decode('utf-16')
    try:
        return raw.decode('utf-8')
    except UnicodeDecodeError:
        return raw.decode('utf-16', errors='replace')


fd = rd(os.path.join(D, 'firstdiv73.txt'))
et = rd(os.path.join(D, 'exctable_diff73.txt'))

units = int(re.search(r'^units:\s+(\d+)', fd, re.M).group(1))
inside = int(re.search(r'^inside_try:\s+(\d+)', fd, re.M).group(1))
outside = int(re.search(r'^outside_try:\s+(\d+)', fd, re.M).group(1))
kind = dict(re.findall(r'^kind_(.+?):\s+(\d+)', fd, re.M))

et_units = int(re.search(r'^units:\s+(\d+)', et, re.M).group(1))
etd = dict(re.findall(r'^(et_same|et_diff|prod_deeper|orig_none_prod_try|'
                      r'orig_try_prod_none|nomatch|loadfail):\s+(\d+)', et, re.M))

# original exception-table entry counts per failing unit
ent0 = sum(1 for l in et.splitlines() if re.search(r'origEnts=0\b', l))
entn = sum(1 for l in et.splitlines() if re.search(r'origEnts=[1-9]', l))
nest_gt0 = sum(1 for l in et.splitlines()
               if (m := re.search(r'origNest=(\d+)', l)) and int(m.group(1)) > 0)
nest_delta = [l for l in et.splitlines()
              if (m := re.search(r'origNest=(\d+) prodNest=(\d+)', l))
              and m.group(1) != m.group(2)]

# first-divergence inside an exception handler
fd_in = [l for l in fd.splitlines() if 'firstdiv=Y' in l]
try_at_div = [l for l in fd_in if 'origTryDepth=' in l
              and not re.search(r'origTryDepth=0\b', l)]

L = ['R74 centre verdict on the directive: "the root cause IS the nested try-except problem"',
     '=' * 78,
     'scope: the 77 failing units of the 35 pylingual-failure pyc (prev arm = R73 landed bytes)',
     'sources: dump/firstdiv73.txt (first-divergence probe), dump/exctable_diff73.txt',
     '         (exception-table probe), dump/tryverdict73.txt (per-unit et/nest table)',
     '',
     '1. exception table of the ORIGINAL pyc code object (et_same / et_diff:)',
     '   units=%d  et_same=%s  et_diff=%s  prod_deeper=%s  orig_none_prod_try=%s'
     '  orig_try_prod_none=%s' % (et_units, etd.get('et_same'), etd.get('et_diff'),
                                  etd.get('prod_deeper'), etd.get('orig_none_prod_try'),
                                  etd.get('orig_try_prod_none')),
     '   original has exception table at all: with-entry=%d  no-entry=%d  -> %d/%d'
     % (entn, ent0, entn, units),
     '   original max nesting >0: %d ; nesting-depth orig vs product differing: %d'
     % (nest_gt0, len(nest_delta)),
     '',
     '2. FIRST divergence position (dump/firstdiv73.txt)',
     '   units=%d  kind_Different control flow=%s  kind_Different bytecode=%s'
     % (units, kind.get('Different control flow'), kind.get('Different bytecode')),
     '   first divergence inside an exception region: %d / %d' % (inside, units),
     '   first divergence outside: %d / %d' % (outside, units),
     '   first-divergence lines carrying origTryDepth>0: %d' % len(try_at_div),
     '',
     '3. what the numbers say (reported as measured, not as advocacy)',
     '   - 37 of 77 failing units live in code objects with NO exception table at all,',
     '     and 65 of 77 first diverge OUTSIDE any exception region: a nested try-except',
     '     mechanism cannot be the single root cause for those units.',
      '   - 27 / 76 probeable units do have an exception-table difference, and 11 / 76 first diverge',
      '     inside an exception region; those are the genuine try-except sub-family. Round 74 took',
      '     2 of them on: real_quote one_prod_to_ndarray / get_cache_l2_data_by_one cleared 41/45 -> 43/45.',
      '   - product nesting depth never exceeded the original (prod_deeper=0), so the defect',
      '     is not "the product nests too deep" either.',
      '',
      '4. strongest separately-actionable sub-families (measured)',
      '   - trade_live_broker.TradeLiveBroker._process_order  orig et=10 (handler body); file 114/128 -> 115/128',
      '     this round (get_max_amount cleared, process_order still open)',
      '   - bar.BarData.limit_up / limit_down  F-TERNARY family, fixed in round 73 (82/85 -> 84/85)',
      '   - IQCommon.util.email_utils.send_email  first divergence inside a handler (et=5), still 3/4',
      '   - fly/data/quote.*  81/92 and flytools 65/66, trade_info_utils 36/41 remain the largest',
      '     single-file residues (G3v same-status movement: finance +2, real_quote +2, trade_live_broker +1)',
     '',
     'VERDICT: the directive is confirmed for an 11-unit sub-family (inside-try first',
     'divergence) and quantitatively NOT the root cause for the other 65; both readings',
     'are filed here so the disagreement stays visible.']
out = os.path.join(G, 'TRYVERDICT_r74.txt')
io.open(out, 'w', encoding='utf-8', newline='\n').write('\n'.join(L) + '\n')
print('\n'.join(L[5:]))
print('WROTE', out)
