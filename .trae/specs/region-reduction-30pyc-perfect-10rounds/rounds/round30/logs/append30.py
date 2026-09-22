# -*- coding: utf-8 -*-
"""Append the Round 30 block to tasks.md byte-level (pure CRLF, no BOM change).

Every figure is read from the archived logs of this round by an asserted regex -- nothing is
typed from memory.  Run without --apply for a dry run.
"""
import hashlib
import io
import json
import os
import re
import sys

REPO = r'F:\Downloads\pythoncdc-main'
TASKS = os.path.join(REPO, r'.trae\specs\region-reduction-30pyc-perfect-10rounds\tasks.md')
LOGS = os.path.join(REPO, r'.trae\specs\region-reduction-30pyc-perfect-10rounds\rounds\round30\logs')


def rd(name):
    return io.open(os.path.join(LOGS, name), encoding='utf-8').read()


raw = io.open(TASKS, 'rb').read()
assert raw[:3] != b'\xef\xbb\xbf', 'tasks.md must have no BOM'
text = raw.decode('utf-8')
assert raw.count(b'\r\n') == raw.count(b'\n'), 'tasks.md must be pure CRLF (found lone LF)'
before_lines = text.count('\n')
prefix = hashlib.sha256(raw).hexdigest()[:16]
assert '- [x] Task 29:' in text and 'Task 30' not in text, 'unexpected tasks.md state'

# ---- G7 stats, read from stats30.txt ---------------------------------------------------
stats = rd('stats30.txt')
pat = (r'total_pyc\s*:\s*(?P<total>\d+).*?verified_pyc\s*:\s*(?P<verified>\d+).*?'
       r'ok_pyc\s*:\s*(?P<ok>\d+).*?partial_pyc\s*:\s*(?P<partial>\d+).*?'
       r'failed_pyc\s*:\s*(?P<failed>\d+).*?'
       r'total_functions\s*:\s*(?P<tf>\d+).*?matched_functions\s*:\s*(?P<mf>\d+).*?'
       r'cumulative_match_rate\s*:\s*(?P<rate>[\d.]+)%')
m = re.search(pat, stats, re.S)
assert m, 'stats regex did not match:\n' + stats[-800:]
g7 = ('`total_pyc {total} / verified_pyc {verified} / ok_pyc {ok} / partial_pyc {partial} / '
      'failed_pyc {failed} / total_functions {tf} / matched_functions {mf} / '
      'cumulative_match_rate {rate}%`').format(**m.groupdict())
assert int(m.group('ok')) + int(m.group('partial')) + int(m.group('failed')) == int(m.group('total'))
assert int(m.group('tf')) == 5746, 'function count moved: %s' % m.group('tf')

# ---- G6 batch, read from batch_all30.txt -----------------------------------------------
batch = rd('batch_all30.txt')
mb = re.findall(r'\[(\d+)/(\d+)\]', batch)
assert mb and mb[-1] == ('402', '402'), 'batch did not finish: %s' % (mb[-1:] or 'none')
assert sum(1 for l in batch.splitlines() if l.startswith('[BATCH] index written back')) == 1
assert 'G6 完成判据' in batch

# ---- G4 tally, read from g4_ab402_sha.txt ----------------------------------------------
g4 = rd('g4_ab402_sha.txt')
tg4 = re.search(r'TALLY SAME=(\d+) IMPROVED=(\d+) REGRESSION=(\d+) MOVED=(\d+) ERR=(\d+)', g4)
assert tg4 and tg4.groups() == ('401', '0', '0', '1', '0'), tg4.groups()
assert "gained=[\"['events', 510, 508, 2, 157]\"]" in g4 and "['events', 510, 491, 2, 157]" in g4


def tally(name):
    t = re.search(r'\{"SAME": (\d+), "IMPROVED": (\d+), "REGRESSION": (\d+), "MOVED": (\d+), '
                  r'"other": (\d+)\}', rd(name))
    assert t, name
    return t.groups()


assert tally('g2prime_38.txt') == ('38', '0', '0', '0', '0')
assert tally('g3_96.txt') == ('96', '0', '0', '0', '0')
assert tally('e_g2prime_38.txt') == ('38', '0', '0', '0', '0')
assert tally('e_g3_96.txt') == ('96', '0', '0', '0', '0')
e4 = re.search(r'TALLY SAME=(\d+) IMPROVED=(\d+) REGRESSION=(\d+) MOVED=(\d+) ERR=(\d+)',
               rd('e_g4_ab402_sha.txt'))
assert e4 and e4.groups() == ('402', '0', '0', '0', '0'), e4.groups()

# ---- G0/G1 repro readings --------------------------------------------------------------
def g1read(name):
    out = {}
    for l in io.open(os.path.join(LOGS, name), encoding='utf-8'):
        r = json.loads(l)
        out[os.path.basename(r['path'])] = (r['matched_functions'], r['total_functions'], r['mism'])
    return out


head, cand = g1read('g1b_head.jsonl'), g1read('g1b_c1.jsonl')
assert head['r30c_w2.pyc'][:2] == (3, 6) and cand['r30c_w2.pyc'] == (6, 6, [])
assert head['r30c_witness.pyc'] == (6, 6, []) and cand['r30c_witness.pyc'] == (6, 6, [])
wm = {r[0]: r[1:] for r in head['r30c_w2.pyc'][2]}
assert sorted(wm) == sorted(['w_a_true_break_epilogue', 'w_b_true_break_yield_epilogue', 'w_e_deep'])
assert wm['w_a_true_break_epilogue'] == [27, 21, 1, 11] and wm['w_e_deep'] == [30, 26, 0, 30]

idd = rd('index_delta30.txt')
assert 'total fields touched: [\'last_tested_round\']' in idd
nreal = re.search(r'real \(non round-stamp\) field changes: (\d+) -> \[\]$', idd, re.M).group(1)
assert nreal == '0', nreal

pool = rd('pool30.txt').splitlines()
assert pool[0].startswith('baseline(landed round29 index): files 402 partial 32 sum_deficit 104'), pool[0]

BLOCK = u'''
- [x] Task 30: 落地 R30-C1 —— 内层 loop 的 break 角色核验不得认领「终止指令是跳向别处头部的向后
      跳转」的块（原则 2 每块唯一归属 · break 角色侧，只删不增），修
      `IQEngine/plugins/plugin_system_event_source/default_event_source.pyc :: events` 被吞掉的
      17 条外层循环体尾语句，严格尺缺口 −19 → −2
  - [x] SubTask 30.1: 目标池按落地字节（基线 `06f0ba50`）重建：partial 32 / Σdeficit 104 /
          deficit-1 共 8 个（`logs/pool30.txt` 逐条存档）。三条诊断线并行，各在私有 scratch 目录，
          未碰仓库、未碰 `core/`：线 A 异常尾声发射侧、线 B 汇合块的源级嵌套归属、线 C `events −19`。
  - [x] SubTask 30.2: 线 A **判据否证**，并拆开 Round 28 的「同族」归并（`logs/diagA_ANALYSIS.md`）：
          候选 R30-A（预消解侧拒绝消费 bare-return-None 尾声）改进 0 —— 靶子
          `risk_calculation/function.pyc :: save_testds_to_json` 只把缺的副本移到函数尾（仍 310），
          却在合成锚 `r2_09_bool_cond_invert_dec*` 上造成**真回归 102/102 → 96/80** ⇒ REJECTED；
          且对 `fly/common/flytools.pyc :: FileLock.acquire` 产物**字节零改动**（其尾声载荷是
          `STORE/DELETE e` 的 `except-as e` 清理而非 `return None`，并混着裸 raise 迁移与环尾回边
          丢失）⇒ 两个靶子是两族，各需一条自己的发射侧判据，原样移交。
  - [x] SubTask 30.3: 线 B 门禁齐备但**不占本轮槽位**（`logs/diagB_ANALYSIS.md`）：R30-B3 在 98
          文件窗 sha 级 `SAME=97 REGRESSION=0 MOVED=1`、严格尺把 `load_daily :: <module>` 的
          `target_diff → CLEAN`（文件 clean `22/25 → 23/25`），但全 402 官方尺 `SAME=402
          IMPROVED=0 REGRESSION=0 MOVED=0` —— 完全中性，且 G0 与 Round 29 同样不可得（缺陷在分析器
          对原始字节码布局的读取，源级合成落不进那个状态）；判据与 spec 原样移交。同轮另实测：语料外
          见证 `r29x_01_module_if_deficit_witness.pyc :: <module> 142/138` 的损伤是
          `for row in (payload or [1,2])` 的 or 链被从 for 迭代头吸走，**不是**汇合块形状，
          B 线任何判据都翻不动它。
  - [x] SubTask 30.4: 线 C 的根因位置由**打戳镜像**实测确定（`logs/diagC_ANALYSIS.md`）：靶子里被吞
          的块 @3214 同时被三处认领（`[Q] region_ast_generator.py L4216 / L6469 / L20469`），因此
          发射侧收窄任何一处认领都被其余两处抵消（实测臂 `candc`：`SAME=2 IMPROVED=0`）—— 本轮的
          决定性负结果，修必须落在分析器侧那一次 break 认领上。同轮否证「events 属 Round 24 整块丢失
          族」的归并：它是 17 条少排 ＋ 15 条错排 ＋ 一个 2 指令第三形状，没有单条 block-loss 判据
          能覆盖。
  - [x] SubTask 30.5: 落 R30-C1（`core/cfg/region_analyzer.py:4098`，`git diff --numstat` = 11 0，
          纯 CRLF 保持、该文件本就无 BOM，落地后与测量镜像 `mirr_c1c` **sha256 逐字节相同**
          `7ee4151d31faf41b8202…`，1673044 → 1674078 字节）：break 候选核验循环里插入
          `_r30c1_last = break_block.get_last_instruction()` ＋「若 `_r30c1_last.opname in
          BACKWARD_JUMP_OPS` 且 `_r30c1_last.argval != header.start_offset` 则 `continue`」。
          候选 break 块是离开本区域的块，若其终止指令属向后跳转类而落点不是本区域头部，
          那条边属于**外层** loop，本区域不得核验它、不得并入 `region_blocks`，也就不会经批量入账
          变成无人发射的块。判据只读块自身（终止指令 opname 类＋落点与头部块的同一性），不读偏移
          常量／名字／条数／函数名；与同块上方 9 行处既有的**后继侧镜像**判据（`_rs.start_offset ==
          _rl.argval` 者是本 loop 回边，不是出口）共用同一 helper 与同一 op 类常量，是既有 idiom 的
          对称缺失。只删不增，不命中时逐字节不变。
  - [x] SubTask 30.6: 门禁（严格串行，原始日志 `rounds/round30/logs/`）：**G0 取得**（本轮与前两轮
          不同，有语料外复现）——`test_repros/round30_enclosing_loop_backedge_break/r30c_w2.pyc`
          落地核 `3/6`（`w_a_true_break_epilogue 27/21`、`w_b_true_break_yield_epilogue 23/19`、
          `w_e_deep 30/26`）→ 判据后 `6/6 mism=[]`；CONTROL 电池 `r30c_witness.pyc` 两核均 `6/6`
          且产物 **sha 逐字节相同** `ef52a76276145780`（内层自己的回边／真 forward break／for 套
          for 的 break／`while True` 破出后无区域出口块四条邻位全部不动）。G1′ 语料靶子 `events
          510/491 → 510/508`；G2′ 前轮 38 复现电池 `SAME=38`、G3 前轮 96 锚点电池 `SAME=96`、
          两者 IMPROVED=REGRESSION=MOVED=ERR=0；G4 全量 A/B（**sha 优先**）
          `SAME=401 IMPROVED=0 REGRESSION=0 MOVED=1 ERR=0`，完全匹配文件 370/370，唯一 MOVED 即
          靶子且只朝真值方向移动；G4′ 唯一变化产物严格尺 `512/493 (−19, 4 hunk) → 512/510 (−2,
          2 hunk)`、文件级 clean 13/14 与 sigma 不变 ⇒ STRICT-BETTER；G4″ 一手产物间差分：c1 相对
          head **只有一段 17 条插入**（@3210..3314）、零删除；G5′ 落地形等价性：带注释镜像去掉 5 行
          注释即与测量臂逐字节相同，且 38/96/402 三档 `SAME=38/96/402 MOVED=0`；G5 `single` 靶子
          仍 `13/14`（缺口由 19 条指令降到 2 条，未翻转），金丝雀 `load_daily.pyc 23`、
          `quotation.pyc 143`、`plugin_system_persist/__init__.pyc 15`、`custom_tools.pyc 6` 全保持。
  - [x] SubTask 30.7: `batch --index pyc_index.json --all --round 30` 全量复验把索引拉回实测
          （`logs/batch_all30.txt`，`[402/402]` 跑完、索引回写标记恰 1 次、Traceback／
          KeyboardInterrupt／MemoryError 0 行，完成性判据已附在日志末行），`stats` 读数存
          `logs/stats30.txt`：''' + u' ' + g7 + u'''；索引改动逐字段核对见 `logs/index_delta30.txt`
          （本轮只有 `last_tested_round` 29→30 共 402 条，其余字段实测改动 ''' + nreal + u''' 条；
          受跟踪产物变化 1 份 = 靶子的 `default_event_sourceOK.py`，其 sha 与测量臂产物逐字节相同
          `e80b5b38f0146f2b`）。
  - [x] SubTask 30.8: 移交 Round 31：① 靶子剩余 −2（`orig@3208..3212` 的
          `JUMP_FORWARD <exit> / JUMP_BACKWARD <inner header>` 两连；若那条死回边无法从任何忠实
          源码重新生成，`events` 就有 −2 下限 —— 需自己的轮次判定，不要在门禁轮里补跳转发射）；
          ② R30-C2（父 loop 按原则 4 移交子 loop 区域时，fall-through 序中排在子区域之前的裸体块
          必须先就地渲染）证据齐备未落地：单用计数中性 `491→491`，与 C1 同用可把严格尺压到只剩
          1 个非相等块、官方尺 `true_diffs 157→31`，代价 `jump_diffs 2→4` ＋ 22 行源码；
          ③ R30-B3（线 B，汇合块两臂同时取消认领）全套门禁与 spec；④ 异常尾声族按本轮拆出的两族
          各需一条发射侧判据（`function.pyc 14/15`、`flytools.pyc 64/65`）；⑤ 未动残余
          `DefaultMatcher.match`、`clock_worker +16`、`decrypt_database_url +29`、
          `instance._init_config −1`、`strategy.pyc` 两条、`quote.pyc` f-string 族与
          `load_bars_from_hundsun 477/470`、语料外见证 `r29x_01 <module> 142/138`；
          ⑥ 电池基线 `anchors96.txt` ＋ 38 复现继续承重，承重锚点新增
          `test_repros/round30_enclosing_loop_backedge_break/r30c_w2.pyc`（落地核必须 `3/6`、
          判据后 `6/6`）与 `r30c_witness.pyc`（两核必须 `6/6` 且产物 sha `ef52a76276145780`），
          `default_event_source.pyc` 自本轮起必须 `13/14` 且 `events` 缺口 ≤2；
          `load_daily.pyc` 23、`quotation.pyc` 143、`plugin_system_persist/__init__.pyc` 15、
          `custom_tools.pyc` 6 不变。重生成合成件时注意 `py_compile` 默认只写 `__pycache__`，
          电池读的是同名同级 `.pyc`，必须显式传 `cfile`。
'''
BLOCK = BLOCK.replace('\n', '\r\n')
for i, l in enumerate(BLOCK.split('\r\n')):
    if '\r' in l:
        print('CR on line %d: %r' % (i, l[:160]))
assert BLOCK.count('\r\n') == BLOCK.count('\n') and '\r\r\n' not in BLOCK

out = (text + BLOCK).encode('utf-8')
if '--apply' in sys.argv:
    io.open(TASKS, 'wb').write(out)
    chk = io.open(TASKS, 'rb').read()
    assert chk == out
    assert chk.count(b'\r\n') == chk.count(b'\n'), 'appended file is not pure CRLF'
    print('tasks.md appended: %d -> %d bytes, lines %d -> %d, prefix-sha256(before)=%s'
          % (len(raw), len(chk), before_lines, chk.count(b'\r\n'), prefix))
    print('G7 row:', g7)
else:
    print('dry run; would append %d CRLF lines; G7 row: %s' % (BLOCK.count('\r\n'), g7))
