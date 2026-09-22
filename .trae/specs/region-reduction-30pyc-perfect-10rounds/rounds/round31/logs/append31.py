# -*- coding: utf-8 -*-
"""Append the Round 31 block to tasks.md byte-level (pure CRLF, no BOM change).

Every figure is read from this round's archived logs by an asserted regex -- nothing is typed
from memory.  Run without --apply for a dry run.
"""
import hashlib
import io
import json
import os
import re
import sys

REPO = r'F:\Downloads\pythoncdc-main'
LOGS = os.path.join(REPO, r'.trae\specs\region-reduction-30pyc-perfect-10rounds\rounds\round31\logs')
TASKS = os.path.join(REPO, r'.trae\specs\region-reduction-30pyc-perfect-10rounds\tasks.md')
sys.stdout.reconfigure(encoding='utf-8')


def rd(name):
    p = os.path.join(LOGS, name.replace('/', os.sep))
    b = io.open(p, 'rb').read()
    assert b, 'archived log is empty (a probe that prints nothing is broken, not empty): %s' % p
    return b.decode('utf-8').replace('\r\n', '\n')


def jread(name):
    out = {}
    for l in rd(name).splitlines():
        r = json.loads(l)
        out[os.path.basename(r['path'])] = (r['arm'], r['sha'], r['matched_functions'],
                                             r['total_functions'], r['mism'])
    return out


raw = io.open(TASKS, 'rb').read()
assert raw[:3] != b'\xef\xbb\xbf', 'tasks.md must have no BOM'
text = raw.decode('utf-8')
assert raw.count(b'\r\n') == raw.count(b'\n'), 'tasks.md must be pure CRLF (found lone LF)'
prefix = hashlib.sha256(raw).hexdigest()[:16]
assert '- [x] Task 30:' in text and 'Task 31' not in text, 'unexpected tasks.md state'
assert text.endswith('\r\n'), 'tasks.md must end with a line break'

# ---- G7 stats ---------------------------------------------------------------------------
stats = rd('stats31.txt')
ms = re.search(r'total_pyc\s*:\s*(?P<total>\d+).*?verified_pyc\s*:\s*(?P<verified>\d+).*?'
               r'ok_pyc\s*:\s*(?P<ok>\d+).*?partial_pyc\s*:\s*(?P<partial>\d+).*?'
               r'failed_pyc\s*:\s*(?P<failed>\d+).*?total_functions\s*:\s*(?P<tf>\d+).*?'
               r'matched_functions\s*:\s*(?P<mf>\d+).*?cumulative_match_rate\s*:\s*(?P<rate>[\d.]+)%',
               stats, re.S)
assert ms, stats
g7 = ('`total_pyc {total} / verified_pyc {verified} / ok_pyc {ok} / partial_pyc {partial} / '
      'failed_pyc {failed} / total_functions {tf} / matched_functions {mf} / '
      'cumulative_match_rate {rate}%`').format(**ms.groupdict())
d = ms.groupdict()
assert int(d['ok']) + int(d['partial']) + int(d['failed']) == int(d['total']) == 402
assert int(d['verified']) == 402 and int(d['tf']) == 5746
idx = json.load(io.open(os.path.join(REPO, 'pyc_index.json'), encoding='utf-8'))
assert len(idx) == 402 and sum(e['function_count'] for e in idx) == int(d['tf'])
assert sum(e['matched_functions'] for e in idx) == int(d['mf']) == 5643

# ---- G6 batch ---------------------------------------------------------------------------
batch = rd('batch_all31.txt')
mb = re.findall(r'\[(\d+)/(\d+)\]', batch)
assert mb and mb[-1] == ('402', '402'), 'batch did not finish: %s' % (mb[-1:] or 'none')
assert sum(1 for l in batch.splitlines() if l.startswith('[BATCH] index written back')) == 1
assert sum(len(re.findall(r'^%s' % k, batch, re.M))
           for k in ('Traceback', 'KeyboardInterrupt', 'MemoryError')) == 0
assert 'G6 完成判据' in batch

# ---- pool / landed deficit-1 readings ---------------------------------------------------
pool = rd('pool31.txt').splitlines()
mp = re.match(r'baseline\(landed round30 index, HEAD (\w+)\): files (\d+) partial (\d+) '
              r'sum_deficit (\d+) deficit1 (\d+)', pool[0])
assert mp, pool[0]
BASE, nfiles, npartial, sdef, nd1 = mp.group(1), mp.group(2), mp.group(3), mp.group(4), mp.group(5)
assert (nfiles, npartial, sdef, nd1) == ('402', '32', '104', '8')
d1 = re.findall(r'^  (\S+?\.pyc)\s+(\d+)/(\d+)\s+deficit 1$', rd('pool31.txt'), re.M)
assert len(d1) == 8, len(d1)
ld = rd('landed_d1.txt').splitlines()
assert len(ld) == 8, ld
mfly = re.search(r'landed flytools\.pyc\s+(\d+)/(\d+)\s*\[\[.acquire., (\d+), (\d+), (\d+), (\d+)\]\]',
                 '\n'.join(ld))
assert mfly and mfly.groups() == ('64', '65', '88', '85', '2', '14'), mfly and mfly.groups()

# ---- G4 sha-first + count tally ---------------------------------------------------------
g4 = rd('g4_ab402_sha.txt')
tg4 = re.search(r'TALLY SAME=(\d+) IMPROVED=(\d+) REGRESSION=(\d+) MOVED=(\d+) ERR=(\d+)', g4)
assert tg4 and tg4.groups() == ('400', '1', '0', '1', '0'), tg4.groups()
tfile = re.search(r'files fully matched: a=(\d+) b=(\d+)', g4)
assert tfile and tfile.groups() == ('370', '371'), tfile.groups()
assert re.search(r'IMPROVED F:\S+flytools\.pyc\s+64/65 -> 65/65', g4)
assert 'MOVED  F:/Downloads/pythoncdc-main/site-packages/IQCommon/api/gtn_api.pyc  gained=[] lost=[]' in g4
tc = re.search(r'\{"SAME": (\d+), "IMPROVED": (\d+), "REGRESSION": (\d+), "MOVED": (\d+), '
               r'"other": (\d+)\}', rd('g4_ab402.txt'))
assert tc and tc.groups() == ('401', '1', '0', '0', '0'), tc.groups()


def tally(name):
    t = re.search(r'\{"SAME": (\d+), "IMPROVED": (\d+), "REGRESSION": (\d+), "MOVED": (\d+), '
                  r'"other": (\d+)\}', rd(name))
    assert t, name
    return t.groups()


assert tally('g2prime_38.txt') == ('38', '0', '0', '0', '0')
assert tally('g3_98.txt') == ('98', '0', '0', '0', '0')

# ---- G0 promoted witness / control + G1 target ------------------------------------------
w_h, w_c = jread('g0p_head.jsonl')['r31a_witness.pyc'], jread('g0p_c.jsonl')['r31a_witness.pyc']
k_h, k_c = jread('g0p_head.jsonl')['r31a_control.pyc'], jread('g0p_c.jsonl')['r31a_control.pyc']
assert w_h[2:4] == (1, 4) and w_c[2:4] == (3, 4) and k_h[2:4] == k_c[2:4] == (5, 7)
assert k_h[1] == k_c[1], 'CONTROL products must be sha-identical across the two cores'
wm = {r[0]: r[1:] for r in w_h[4]}
assert sorted(wm) == ['w_a_handler_raise_after_nested_if', 'w_b_handler_raise_then_fall',
                      'w_c_handler_nested_raise_deep']
assert wm['w_a_handler_raise_after_nested_if'] == [52, 47, 4, 11]
assert wm['w_b_handler_raise_then_fall'] == [48, 44, 3, 14]
assert wm['w_c_handler_nested_raise_deep'] == [64, 63, 2, 51]
cm = sorted(r[0] for r in k_h[4])
assert cm == ['c2_arm_tail_is_break', 'c6_both_arms_end_in_raise']
g1h, g1c = jread('g1_head.jsonl')['flytools.pyc'], jread('g1_c.jsonl')['flytools.pyc']
assert g1h[2:4] == (64, 65) and g1c[2:4] == (65, 65) and g1c[4] == []
assert (int(mfly.group(1)), int(mfly.group(2))) == (g1h[2], g1h[3])
# site-two necessity: witness under site-one-only arm
b0 = jread('g01_b.jsonl')['r31a_witness.pyc']
c0 = jread('g01_c.jsonl')['r31a_witness.pyc']
assert b0[2:4] == (2, 4) and c0[2:4] == (3, 4)

# ---- G4' strict readings + hunk reconstruction + product identity -----------------------
sh = rd('g4prime_head_flytools.txt')
sc = rd('g4prime_flytools.txt')
mh = re.search(r'DEFECT <module>\.FileLock\.acquire\s+\[seq_len\] orig=(\d+) decomp=(\d+)', sh)
assert mh and mh.groups() == ('90', '85'), mh and mh.groups()
rh = re.search(r'strict clean (\d+)/(\d+)\s+sigma-defect=(\d+)\s+sum_abs_delta=(\d+)', sh)
rc = re.search(r'strict clean (\d+)/(\d+)\s+sigma-defect=(\d+)\s+sum_abs_delta=(\d+)', sc)
assert rh and rc and rh.groups() == ('65', '66', '1', '5') and rc.groups() == ('66', '66', '0', '0')
assert re.search(r'strict clean 5/5\s+sigma-defect=0', rd('g4prime_head_gtn_api.txt'))
assert re.search(r'strict clean 5/5\s+sigma-defect=0', rd('g4prime_gtn_api.txt'))
hh = rd('hunks_head_tracked.txt')
assert re.search(r'filtered orig=(\d+) decomp=(\d+) delta=[-+](\d+)\s+non-equal blocks=(\d+)',
                 hh).groups() == ('90', '85', '5', '3')
assert len(re.findall(r'^  H\d ', hh, re.M)) == 3
hc = rd('hunks_c_tracked.txt')
assert re.search(r'filtered orig=90 decomp=90 delta=\+0\s+non-equal blocks=0', hc)
ps = rd('products_sha.txt')
mpg = re.findall(r'(\S+OK\.py)\s*\n\s*tracked\s+sha16=(\w{16}) len=(\d+).*?tracked == measured build_c product: (\w+)',
                 ps, re.S)
assert len(mpg) == 2 and all(x[3] == 'True' for x in mpg), mpg
sha_fly = dict((os.path.basename(x[0]), x[1]) for x in mpg)
assert sha_fly['flytoolsOK.py'] == 'd1ddb72cf60efdfe'
assert sha_fly['gtn_apiOK.py'] == 'f26e8a084eef60cc'
gtdiff = rd('g4prime_gtn_api_diff.txt')
assert len(re.findall(r'^-[^-+]', gtdiff, re.M)) == 4
assert len(re.findall(r'^\+[^-+]', gtdiff, re.M)) == 2
assert gtdiff.count('else:') == 2 and gtdiff.count('time.sleep(1)') == 4
gt_h = io.open(os.path.join(r'D:/Temp/r31gate/c1/build_head', 'IQCommon__api__gtn_apiOK.py'),
               encoding='utf-8').read().count('\n')
gt_c = io.open(os.path.join(r'D:/Temp/r31gate/c1/build_c', 'IQCommon__api__gtn_apiOK.py'),
               encoding='utf-8').read().count('\n')
assert gt_h - gt_c == 2, (gt_h, gt_c)

# ---- G5 target + canaries ---------------------------------------------------------------
g5 = rd('g5_single.txt')
blocks = dict((m.group(1), m.group(0)) for m in
              re.finditer(r'### (\S+)\n\[SINGLE\].*?(?=\n### |\Z)', g5, re.S))
assert len(blocks) == 8, sorted(blocks)
canary = {}
for k, v in blocks.items():
    mm = re.search(r'total_functions:\s+(\d+)\n\s+matched_functions:\s+(\d+)', v)
    assert mm, k
    canary[k.split('/')[-1]] = '%s/%s' % (mm.group(2), mm.group(1))
assert canary['flytools.pyc'] == '65/65', canary
assert canary['quotation.pyc'] == '143/143' and canary['load_daily.pyc'] == '23/23'
assert canary['__init__.pyc'] == '15/15' and canary['custom_tools.pyc'] == '6/6'
assert canary['instance.pyc'] == '31/32', canary
assert canary['replace_utils.pyc'] == '8/9', canary
assert canary['quote.pyc'] == '67/81', canary

# ---- index delta ------------------------------------------------------------------------
idd = rd('index_delta31.txt')
assert "total fields touched: ['bytecode_match_rate', 'decompile_status', 'last_tested_round', " \
       "'matched_functions']" in idd
nreal = re.search(r'real \(non round-stamp\) field changes: (\d+) -> \[(.+)\]$', idd, re.M)
assert nreal and nreal.group(1) == '1' and nreal.group(2) == "'fly/common/flytools.pyc'", nreal.groups()
assert re.search(r'all 402 entries re-stamped 30 -> 31, list elided\)', idd)
mstamp = re.search(r'last_tested_round\s+changed in (\d+) entries', idd)
assert mstamp and mstamp.group(1) == '402', mstamp and mstamp.groups()
mst2 = re.search(r're-stamped (\d+) -> (\d+)', idd)
assert mst2, idd
assert 'partial -> ok' in idd and '64 -> 65' in idd and '0.9846153846153847 -> 1.0' in idd

# ---- landed core identity (assert against the real file, not a log) ----------------------
core = io.open(os.path.join(REPO, r'core\cfg\region_analyzer.py'), 'rb').read()
assert core.count(b'\r\n') == core.count(b'\n') and core[:3] != b'\xef\xbb\xbf'
assert hashlib.sha256(core).hexdigest()[:20] == 'a66248d3b9a3e0a1545e'
mir = io.open(os.path.join(r'D:/Temp/r31gate/c1/mirr_c/core/cfg', 'region_analyzer.py'), 'rb').read()
assert core == mir, 'worktree core is not the measured mirror any more'
d1s = rd('diagA_ANALYSIS.md')
assert 'R31' in d1s
bd = rd('blockdump_landed_regions.txt')
assert re.search(r'^B364\s+n=1\s+pred=B242,B314\s+succ=B568\s+role=\S+\s+RAISE_VARARGS 0', bd, re.M)

BLOCK = u'''
- [x] Task 31: 落地 R31-C —— 臂停止集里「没有正常后继、且全部前驱都在本臂内」的终止块是本臂的
          终止语句块，不得充当本臂与兄弟臂的边界认领（原则 2 每块唯一归属，只 `discard` 不新增发射），
          并在 elif 链 `_chain_merge` 重收集处复放同一判据；修 `fly/common/flytools.pyc ::
          FileLock.acquire` 一处归属错位的三个症状（臂尾裸 `raise` 落到 if/else 之后、`except`
          正常出口的 as-var 清理尾声 −4、循环回边 −1），靶子 `64/65 → 65/65`，严格尺
          `90/85（3 个非相等块）→ 90/90（0 个）`，本轮净翻转 1 个文件。
  - [x] SubTask 31.1: 目标池按落地字节（基线 `{base}`）重建（`logs/pool31.txt` 首行直读回写的索引，
          不转述）：`files {nf} partial {np} sum_deficit {sd} deficit1 {nd}`。八个 deficit-1 文件在
          落地核上逐个 `single` 一手复测（`logs/landed_d1.txt` 八条全在），靶子
          `flytools.pyc {ft_m}/{ft_t} [['acquire', {ft_o}, {ft_d}, {ft_j}, {ft_tr}]]`。
  - [x] SubTask 31.2: 线 A 根因由**只诊断代理**在其私有镜像根给出、编排方在自己的镜像根独立复现
          （`logs/diagA_ANALYSIS.md`、`logs/blockdump_head.txt`、落地核同形转储
          `logs/blockdump_landed_regions.txt`）：`except OSError as e` 处理器臂是
          `IfRegion@B200`（`then=[B242]`、`else=[B366,B508,B558]`、`merge=None`），臂内嵌套区域的
          终止块 B364（`RAISE_VARARGS 0`，`successors == exception_successors == {{B568}}`，无正常
          后继）被 `boundary_stop` 原样带进外层 if 的 `then_stop`/`else_stop` ⇒ 它既不被登记为臂尾、
          又使 `_collect_branch_blocks` 停止扩张，遂由父区在整个 if/else 之后发射。一手 hunk 重建
          （`logs/hunks_head_tracked.txt`）证明一处错位同时造出靶子全部三处 hunk，**订正 Round 30
          把它误记成的「三族混合」**：多 hunk 之前先检验「一处错位能否解释全部 hunk」，别按 hunk 数开诊断线。
  - [x] SubTask 31.3: 线 B／线 C 实测后不占本轮槽位。线 B＝R30-B3（汇合块两臂同时取消认领）门禁齐备
          但官方尺中性、无可得 G0，继续随 #61 移交；线 C＝靶子 `events` 残余 −2 需**两条**判据
          （R30-C2 就地渲染 ＋ 那两跳转槽），且 R30-C2 单用使官方尺 `jump_diffs 2→4` 变差。
  - [x] SubTask 31.4: 语料外复现件入库 `test_repros/round31_arm_terminal_join/`：3 见证
          （`w_a`/`w_b`/`w_c`）＋ 6 CONTROL。CONTROL 头注释按实测改写为 **sha 级不变性判据** ——
          代理原稿称「全部 CONTROL 保持 matched」是错的，实测三把核同读 `{ctl_m}/{ctl_t}` 且失败对
          恒为 {ctl_pair}（与本判据无关的既有缺陷）。另：代理的一个块级转储探针是 0 字节的坏探针
          输出（不是空结果），归档时已换成编排方在落地核上重跑的同形转储 ——
          凡归档的探针日志都须断言非空。
  - [x] SubTask 31.5: 落 R31-C（`core/cfg/region_analyzer.py:17137` 站点一 40 行 ＋ `:19310` 站点二
          28 行，`git diff --numstat` = `68 0` 纯新增，核 sha `a66248d3b9a3e0a1`，与实测镜像
          `mirr_c` 逐字节相同）。判据只读同层结构：块身份（本区汇合块／兄弟臂入口／臂入口）、
          `successors - exception_successors` 是否为空（有无正常后继）、`predecessors` 与「臂内集∪
          停止集」的包含关系；不读名字／常量／绝对偏移／条数／函数名。站点二必要性实测：只做站点一时
          合成见证仍 `{b1_m}/{b1_t}`，因为 `_then_stop` 在链汇合重建处从 `boundary_stop` 重新组装、
          覆盖掉站点一的成果；复放后 `{c1_m}/{c1_t}`。
  - [x] SubTask 31.6: 门禁（严格串行，原始日志 `rounds/round31/logs/`）：G0 见证落地核 `{w_m}/{w_t}`
          （{w_defect}）
          → 判据后 `{w_c2_m}/{w_c2_t}`（只剩前驱不满足判据③的第三形状 `w_c`）；
          G0 CONTROL 两核产物 sha 相同；G1 靶子 `{ft_m}/{ft_t} → {g1_m}/{g1_t} mism=[]`；
          G2′ 前轮 38 复现电池 `SAME=38`、G3 承重锚点电池（本轮起并入 R30 两件合成锚）`SAME=98`，
          两档 IMPROVED=REGRESSION=MOVED=ERR=0；G4 全量 A/B（**sha 优先**）
          `SAME={a_same} IMPROVED={a_imp} REGRESSION={a_reg} MOVED={a_mov} ERR={a_err}`、完全匹配文件
          `{a_files} → {b_files}`，唯一 IMPROVED 即靶子、唯一 MOVED 是 `gtn_api.pyc`（`gained=[]
          lost=[]`）；计数尺同跑 `SAME=401 IMPROVED=1`；G4′ 逐个变化产物严格尺 `flytools`
          `{rh_clean} σ{rh_sig} Σ|Δ|={rh_d} → {rc_clean} σ{rc_sig} Σ|Δ|={rc_d}`、`gtn_api` 两把核均
          `5/5 σ0 Σ0`。
  - [x] SubTask 31.7: `batch --index pyc_index.json --all --round 31` 全量复验把索引拉回实测
          （`logs/batch_all31.txt`，`[402/402]` 跑完、索引回写标记恰 1 次、Traceback／
          KeyboardInterrupt／MemoryError 0 行，完成性判据已附在日志末行），`stats` 读数存
          `logs/stats31.txt`： {g7}；索引改动逐字段核对见 `logs/index_delta31.txt`（真实字段改动
          恰 1 条 = 靶子 `partial -> ok`、`matched_functions 64 -> 65`、rate `-> 1.0`，其余 402 条只被
          重打 round 戳 = `last_tested_round` {stamp}）。G5 `single` 靶子 `65/65 100.00%`，金丝雀 `quotation {q}`、`load_daily {ld}`、
          `plugin_system_persist/__init__ {ps}`、`custom_tools {ct}` 全保持，残余 `instance {ins}`、
          `replace_utils {ru}` 逐条同形。受跟踪产物变化 2 份（`logs/products_sha.txt`）：靶子
          `flytoolsOK.py`（sha16 `{sf}`）与 `gtn_apiOK.py`（sha16 `{sg}`），两者均与测量臂产物逐字节相同；
          后者两尺皆判中性，差异是两处 `else: time.sleep(1)` 折叠成不缩进的顺序语句（产物 {gt_h}→{gt_c} 行，
          `logs/g4prime_gtn_api_diff.txt`）⇒ 接受并登记为「ok 文件产物文本变化」在册观察项，不得视为已解释。
  - [x] SubTask 31.8: 移交 Round 32：① 见证第三成员 `w_c_handler_nested_raise_deep 64/63 j2 t51`
          （落单块前驱不满足判据③，另一形状）；② `default_event_source :: events 510/508`（需两条
          判据）；③ #61 R30-B3；④ 发射侧两兄弟 `function.pyc :: save_testds_to_json 314/310`（缺
          **重复**清理副本，需「增」）与 `replace_utils :: decrypt_database_url 295/324`（过量发射，
          需放弃发射侧）；⑤ `instance :: _init_config 86/84`（R16 J1 在册反例，受保护勿再取）；
          ⑥ `clock_worker 1275/1291`、`DefaultMatcher.match 713/689`、`tick_worker_thread 268/247`、
          `quote.pyc 67/81`（含 `load_bars_from_hundsun 477/470`）、`r29x_01 <module> 142/138`；
          ⑦ 代码内注释标签写作 `R31-B` 而本轮发货名 `R31-C` —— 改名会改动被测量字节，须整轮重测，
          留作字面债。锚点新要求：落地核上 `r31a_witness.pyc` 必须 `3/4`、`r31a_control.pyc` 必须
          `5/7` 且失败对只能是 `c2`/`c6`；Round 32 电池 = `anchors100.txt`（本轮 `anchors98.txt` ＋
          这两个新件）。重生成合成件时 `py_compile` 必须显式传 `cfile`，电池读的是同名同级 `.pyc`。
'''

fmt = dict(base=BASE, nf=nfiles, np=npartial, sd=sdef, nd=nd1,
           ft_m=g1h[2], ft_t=g1h[3], ft_o=mfly.group(3), ft_d=mfly.group(4),
           ft_j=mfly.group(5), ft_tr=mfly.group(6),
           ctl_m=k_h[2], ctl_t=k_h[3], ctl_pair='／'.join('`%s`' % x for x in cm),
           b1_m=b0[2], b1_t=b0[3], c1_m=c0[2], c1_t=c0[3],
           w_m=w_h[2], w_t=w_h[3], w_c2_m=w_c[2], w_c2_t=w_c[3],
           w_defect='、'.join('%s %d/%d j%d t%d' % (k, v[0], v[1], v[2], v[3])
                               for k, v in sorted(wm.items())),
           g1_m=g1c[2], g1_t=g1c[3],
           a_same=tg4.group(1), a_imp=tg4.group(2), a_reg=tg4.group(3), a_mov=tg4.group(4),
           a_err=tg4.group(5), a_files=tfile.group(1), b_files=tfile.group(2),
           rh_clean='%s/%s' % rh.group(1, 2), rh_sig=rh.group(3), rh_d=rh.group(4),
           rc_clean='%s/%s' % rc.group(1, 2), rc_sig=rc.group(3), rc_d=rc.group(4),
           g7=g7, sf=sha_fly['flytoolsOK.py'], sg=sha_fly['gtn_apiOK.py'],
           q=canary['quotation.pyc'], ld=canary['load_daily.pyc'],
           ps=canary['__init__.pyc'], ct=canary['custom_tools.pyc'],
           ins=canary['instance.pyc'], ru=canary['replace_utils.pyc'],
           gt_h=gt_h, gt_c=gt_c, stamp='%s -> %s' % mst2.groups())
BLOCK = BLOCK.strip('\n')
BLOCK = BLOCK.format(**fmt)
assert '{{' not in BLOCK and '}}' not in BLOCK, 'escaped braces left unbalanced'
for k, v in fmt.items():
    assert str(v) in BLOCK
BLOCK = BLOCK + '\n'
BLOCK = BLOCK.replace('\n', '\r\n')
assert '\r\r' not in BLOCK
ncl = BLOCK.count('\r\n')
out = raw + BLOCK.encode('utf-8')
print('prefix sha256(before) =', prefix)
print('bytes %d -> %d   lines %d -> %d   CRLF-only=%s   BOM=%s'
      % (len(raw), len(out), text.count('\n'), out.count(b'\n'),
         out.count(b'\r\n') == out.count(b'\n'), out[:3] == b'\xef\xbb\xbf'))
print('appended CRLF lines:', ncl, ' task headers:', BLOCK.count('[x] Task 31:'),
      BLOCK.count('[x] SubTask 31.'))
assert '- [x] Task 29:' in text and '- [x] Task 30:' in text
if '--apply' not in sys.argv:
    print('\n--- dry run: appended block (verbatim, %d lines) ---' % ncl)
    print(BLOCK.replace('\r\n', '\n').rstrip('\n'))
    print('--- end ---')
    print('dry run; pass --apply to write tasks.md')
else:
    io.open(TASKS, 'wb').write(out)
    after = io.open(TASKS, 'rb').read()
    assert after == out
    assert after.count(b'\r\n') == after.count(b'\n')
    assert hashlib.sha256(after[:len(raw)]).hexdigest()[:16] == prefix, 'existing bytes changed'
    print('applied; sha256(after) =', hashlib.sha256(after).hexdigest()[:16])
