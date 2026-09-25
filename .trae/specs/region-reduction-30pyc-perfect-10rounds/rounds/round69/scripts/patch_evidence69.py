# -*- coding: utf-8 -*-
import io

P = (r'F:\Downloads\pythoncdc-main\.trae\specs\region-reduction-30pyc-perfect-10rounds'
     r'\rounds\round69\logs\EVIDENCE.md')
s = io.open(P, encoding='utf-8').read()

r1_old = '`scripts/g0_land69_replay.txt` 为 replay 证据，'
r1_new = ('`logs/gate/Land69_replay_r69.txt`（`scripts/replay69.py` 对 R68 HEAD blob 重推演：'
          '2 文件 `replay == measured mirror bytes: OK` 与 '
          '`repository bytes == replay == mirror: OK`）为 replay 证据，')
assert s.count(r1_old) == 1, ('r1', s.count(r1_old))
s = s.replace(r1_old, r1_new)

r2_old = ('  汇总 `scripts/cadelta69.py` 输出：')
r2_new = ('  汇总 `scripts/cadelta69.py` 输出（第三列 `Sigmajumpdiff` = Σ m[3] = **hunk 计数之和**）：')
assert s.count(r2_old) == 1, ('r2', s.count(r2_old))
s = s.replace(r2_old, r2_new)

reps = [
    ('  d1d:   defects=36 Sigma|d|=254 Sigmajumpdiff=151   （trade_live_broker after_trading_cancel_order 转绿）',
     '  d1d:   defects=36 Sigma|d|=256 Sigmajumpdiff=148   （after_trading_cancel_order 155/155 转绿：hunk 3、true-diff 122 消失；该支 |Δ| 本为 0 ⇒ Σ|Δ| 不变）'),
    ('  d2a:   defects=35 Sigma|d|=197 Sigmajumpdiff=149   （quote 两支转绿 + 一支收窄）',
     '  d2a:   defects=35 Sigma|d|=197 Sigmajumpdiff=150   （quote check_limit/initImagedata 转绿 + get_real_from_zeromq 703/678 → 703/700）'),
    ('  d5i:   defects=37 Sigma|d|=254 Sigmajumpdiff=151   （risk_calc [71,68] -> [71,70]）',
     '  d5i:   defects=37 Sigma|d|=254 Sigmajumpdiff=151   （risk_calc [71,68] → [71,70]，hunk 7 不变、true-diff 19 → 11）'),
]
for o, n in reps:
    assert s.count(o) == 1, (o[:30], s.count(o))
    s = s.replace(o, n)

anchor = '  ```\n'
i = s.find(r2_new)
assert i != -1
j = s.find(anchor, i)          # opening fence of the cadelta block
assert j != -1
k = s.find(anchor, j + 1)      # closing fence
assert k != -1
note = ('\n  ADR-1 归档说明：d1d 为「真缺陷函数转绿」且 Σ|Δ| 不升（256→256）、Σhunk 151→148、'
        '严格 106/123 → 107/123、合成 `r69d1_atco` 2/2 咬合、金丝雀 SAME=4 ⇒ 采纳；'
        'd2a/d5i 按缺失/过冲族判据直接满足（Σ|Δ| 净减 256→197 / 256→254）。')
s = s[:k + len(anchor)] + note + s[k + len(anchor):]

io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print('EVIDENCE patched: r1=%d r2=%d note=%d oldref=%d'
      % (s.count('Land69_replay_r69.txt'), s.count('Sigmajumpdiff = Σ m[3]' in s and 'x' or '第三列'),
         s.count('ADR-1 归档说明'), s.count('g0_land69_replay')))
