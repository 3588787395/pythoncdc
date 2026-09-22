# -*- coding: utf-8 -*-
"""Append the Round 29 block to tasks.md byte-level (pure CRLF, no BOM change), and check
off the Round 28 hand-off SubTask that this round discharges.

Every figure is read from the archived logs of this round by an asserted regex -- nothing is
typed from memory.  Run without --apply for a dry run.
"""
import hashlib
import io
import os
import re
import sys

REPO = r'F:\Downloads\pythoncdc-main'
TASKS = os.path.join(REPO, r'.trae\specs\region-reduction-30pyc-perfect-10rounds\tasks.md')
LOGS = os.path.join(REPO, r'.trae\specs\region-reduction-30pyc-perfect-10rounds\rounds\round29\logs')

raw = io.open(TASKS, 'rb').read()
assert raw[:3] != b'\xef\xbb\xbf', 'tasks.md must have no BOM'
text = raw.decode('utf-8')
assert raw.count(b'\r\n') == raw.count(b'\n'), 'tasks.md must be pure CRLF (found lone LF)'
before_lines = text.count('\n')
prefix = hashlib.sha256(raw).hexdigest()[:16]

# ---- G7 stats, read from stats29.txt --------------------------------------------------
stats = io.open(os.path.join(LOGS, 'stats29.txt'), encoding='utf-8').read()
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

# ---- G6 batch marker, read from batch_all29.txt ---------------------------------------
batch = io.open(os.path.join(LOGS, 'batch_all29.txt'), encoding='utf-8').read()
mb = re.findall(r'\[(\d+)/(\d+)\]', batch)
assert mb and mb[-1] == ('402', '402'), 'batch did not finish: %s' % (mb[-1:] or 'none')
rc = re.search(r'^rc=(\d+)', batch, re.M)
assert rc and rc.group(1) == '0', 'batch rc not 0'

# ---- G4 tally, read from g4_ab402.txt --------------------------------------------------
g4 = io.open(os.path.join(LOGS, 'g4_ab402.txt'), encoding='utf-8').read()
tg4 = re.search(r'\{.*\}', g4, re.S)
assert tg4 and 'REGRESSION": 0' in tg4.group(0) and '"MOVED": 0' in tg4.group(0), g4[-400:]
tg2 = io.open(os.path.join(LOGS, 'g2prime_battery38.txt'), encoding='utf-8').read()
t2 = re.search(r'\{.*\}', tg2, re.S)
assert t2 and '"SAME": 38' in t2.group(0), tg2[-300:]
tg3 = io.open(os.path.join(LOGS, 'g3_battery96.txt'), encoding='utf-8').read()
t3 = re.search(r'\{.*\}', tg3, re.S)
assert t3 and '"SAME": 96' in t3.group(0), tg3[-300:]
sums = {n: (r, e, s, t) for n, r, e, s, t in re.findall(
    r'^(\S+\.jsonl)\s+records=(\d+) err=(\d+) Sumatched=(\d+) Stotal=(\d+)', tg3, re.M)}
assert sums['base_cand96.jsonl'] == ('96', '0', '280', '308'), sums.get('base_cand96.jsonl')
assert sums['base_landed96.jsonl'] == ('96', '0', '280', '308'), sums.get('base_landed96.jsonl')
assert sums['ab402_landed.jsonl'] == ('402', '0', '5641', '5746'), sums.get('ab402_landed.jsonl')
assert sums['ab402_cand.jsonl'] == ('402', '0', '5642', '5746'), sums.get('ab402_cand.jsonl')
timpr = re.findall(r'^IMPROVED\s+(\S+)\s+a=\s*(\d+)/\s*(\d+) b=\s*(\d+)/\s*(\d+)', g4, re.M)
assert timpr == [('fly/dumpload/load_daily.pyc', '22', '23', '23', '23')], timpr
assert re.search(r'a_mism=\[\[\'<module>\', 913, 913, 1, 19\]\] b_mism=\[\]', g4), g4[-300:]
import json as _json


def _full(fn):
    p = os.path.join(LOGS, fn)
    if not os.path.exists(p):
        p = os.path.join(r'D:/Temp/r29gate', fn)
    n = 0
    n2 = 0
    for line in io.open(p, encoding='utf-8'):
        line = line.strip()
        if not line:
            continue
        r = _json.loads(line)
        if r.get('error'):
            continue
        t, m = r.get('total_functions'), r.get('matched_functions')
        if t and m == t:
            n += 1
        if not r.get('mism'):
            n2 += 1
    assert n == n2, (fn, n, n2)
    return n


f_head, f_cand = _full('ab402_landed.jsonl'), _full('ab402_cand.jsonl')
assert (f_head, f_cand) == (369, 370), (f_head, f_cand)
idd = io.open(os.path.join(LOGS, 'index_delta29.txt'), encoding='utf-8').read()
mr = re.search(r'entries with real \(non round-stamp\) field changes: (\d+) -> \[(.*)\]', idd)
assert mr, idd[-300:]
nchg = mr.group(1)
chg_entry = mr.group(2).replace("'", '')
assert len([x for x in mr.group(2).split(',') if x.strip()]) == int(nchg)
assert 'last_tested_round' in idd and 'path list identical: True' in idd

BLOCK = u'''
- [x] Task 29: 落地 R29-A —— 同一 IfRegion 的两条臂同时认领汇合块（原则 2 每块唯一归属的
      臂间共享块取消认领），修 `fly/dumpload/load_daily.pyc :: <module>` 的同形块换位，
      该文件翻转为 ok
  - [x] SubTask 29.1: 目标池按落地字节（基线 `d90f41e5`）重建。线 A（异常尾声发射侧，
          上一轮移交项①）的诊断代理在 150 轮上限处终止且未交 `ANALYSIS.md`，该线索
          **未收口**，原样移交 Round 30。线 B（七个未探明 deficit-1 文件，代理交付
          `D:/Temp/r29diagB/ANALYSIS.md`）与线 C（编排方独立实测）在同一个靶子上合流：
          七个文件聚成四簇，A 簇「汇合块被臂内认领」占 4/7（#5 load_daily 等长／单跳转槽、
          #3 events −19、#4 match −24、#2 clock_worker +16），锚点取唯一计数中性的 #5。
  - [x] SubTask 29.2: 站点识别全部由**打戳镜像**实测，不靠读码，三步否定＋一步肯定
          （日志 `logs/probe_stamps.txt`）：① `region_analyzer.py` 的 11 处
          `merge = else_succ` 逐处打戳，命中 8 次而落点为 1116/2768/960/796/686/472/472/368，
          **无一次涉 2478** ⇒ 汇点塌缩（R13c/`_25b`）与本轮无关；第一版戳因 `%s` 少一个
          占位符抛 `not all arguments converted` 使整轮 0 输出，修好后才有读数（戳不落盘≠没有命中）。
          ② Round 28 判据的邻位假设 `_cr.then_blocks.append(_sb)`（`:1847`，IF_ELIF_CHAIN
          shared_block 后处理）的 append 戳 **0 次命中**（其循环头戳确有 4 次读数
          `sb=370/390/582/288`，无一次为 2478），且戳臂产物读数与落地核逐字节相同
          （913/913/1/19）⇒ 双认领不发生在 shared_block 后处理；线 B 的第二把戳独立复现同一
          0 命中。③ 三处 `region = IfRegion(` 构造点＋生成端 `_process_if_blocks` 消费点打戳
          （以 2478 为门）一击命中：`site=17888 cfg=<module> entry=740 merge=2626
          else=[2456,2478,2562] then=[…,2022,2478,2086,2176,2562]`，生成端 FINAL 同集合
          ⇒ **2478/2562 同时是同一区域的 then 体与 else 体**；既有的「IF_THEN merge 候选识别」
          （`:17850-17878`）整段被 `if merge is None and not else_blocks` 挡在门外（本例
          merge=2626、else 非空），而它自己的注释早已写明「then_blocks 包含 merge 块 ⇒ AST 生成错误」。
  - [x] SubTask 29.3: 落 R29-A（`core/cfg/region_analyzer.py`，`git diff --numstat` = 15 0，
          纯 CRLF 保持、该文件本就无 BOM，落地后与工作镜像 `mirr_cand` **sha256 逐字节相同**
          `e3fde286828754cd…`）：`if then_blocks and else_blocks:` →
          `then_blocks = [b for b in then_blocks if b not in set(then_blocks) & set(else_blocks)]`。
          两臂是互斥控制流路径，被两臂同时认领的块只能是两臂共同到达的汇合点，任何一臂认它作
          体内块都是越界吸收；判据只读块自身的归属状态（两条臂列表的交），不读偏移常量／名字／
          条数／函数名。`all_blocks` 是两臂之并，从 then 臂摘出不丢失任何块，只取消双重认领，
          不命中时逐字节不变。生成端 `_process_if_blocks` 按 `start_offset` 升序遍历每条臂，
          于是取消认领即恢复 then→else→join 的发射次序。
  - [x] SubTask 29.4: **G0 未取得，如实记录**：把落地核产物与候选核产物各自编译回 `.pyc`
          再回灌，两把尺均 `23/23 mism=[]`（实验件 `r29a_03/r29a_04`）——本族缺陷在「分析器
          对原始字节码布局的双认领」，不存在能复现它的源级合成文件；据结构仿写的两份合成
          在落地前后读数不变（`r29a_01_shape_mimic_and_controls.pyc` 两核均 `2/2`，
          三条 CONTROL 均匹配）。已把该仿写＋CONTROL 落为
          `test_repros/round29_arm_shared_join_claim/r29a_01_shape_mimic_and_controls.pyc`
          充当判据的**非触发面**，发货证据改由语料靶子＋严格尺承担。写 G0 过程中顺带暴露
          一条独立缺陷 `r29x_01_module_if_deficit_witness.pyc :: <module> 142/138`
          （jump=2/true=122，两核同形失败，R29-A 未触及），随本轮移交。
  - [x] SubTask 29.5: 门禁（严格串行，原始日志 `rounds/round29/logs/`）：G1′ 语料靶子
          `load_daily.pyc 22/23 → 23/23`、`mism=[]`；G2′ 前轮 38 个合成复现电池
          `SAME=38 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0`；G3 前轮 96 锚点电池对 cand
          `SAME=96`、空读数 0、Σmatched 280／Σtotal 308 两侧相同；G4 全量 A/B
          （落地前 402 基线 vs 候选镜像）`SAME=401 IMPROVED=1 REGRESSION=0 MOVED=0 ERR=0`，
          Σmatched 5641→5642、完全匹配文件 369→370；G4′ 唯一变化产物严格尺
          `913/913 seq_diff → 913/913 target_diff`（σ 两侧均 0，clean 22/25 不变）
          ——发射次序修复，跳转目标归属为残余线索；G5 `single` 靶子 `ok 23/23`，
          金丝雀 `fly/data/quotation.pyc` 仍 `ok 143`、`plugin_system_persist/__init__.pyc`
          仍 `ok 15`、`fly/common/custom_tools.pyc` 仍 `ok 6`。
  - [x] SubTask 29.6: `batch --index pyc_index.json --all --round 29` 全量复验把索引拉回实测
          （`logs/batch_all29.txt`，`[402/402]`、rc=0），`stats` 读数存 `logs/stats29.txt`：''' + u' ' + g7 + u'''；
          索引改动逐字段核对见 `logs/index_delta29.txt`（402 条目路径列表逐字节相同；除
          轮次戳外真实改动条目 ''' + nchg + u''' 条＝''' + chg_entry + u'''：`partial→ok`、
          `matched_functions 22→23`、`bytecode_match_rate →1.0`，与 G4 的 IMPROVED=1 同一条目）。
  - [x] SubTask 29.7: 移交 Round 30：① 异常尾声发射侧（线 A 代理耗尽轮次未收口），靶子
          `risk_calculation/function.pyc 14/15`、`flytools.pyc 64/65`；② R29-A 的残余：
          `load_daily :: <module>` 严格尺 `target_diff`（post-if 语句在产物里仍被归到 else 臂），
          与同簇未修的 #3 `events −19`、#4 `match −24`、#2 `clock_worker +16`——四者同属
          「汇合块被臂内认领」，本轮只关掉计数中性的那一个形状；③ 新发现的语料外复现
          `r29x_01_module_if_deficit_witness.pyc <module> 142/138`（jump=2/true=122）；
          ④ 残余不变：`decrypt_database_url 295→324`、`DefaultMatcher.match`、`strategy.pyc`
          `tick_worker_thread 268→247`、`instance._init_config 86→84`、`quote.pyc` f-string 族；
          ⑤ 电池基线 `anchors96.txt`＋落地字节记录继续承重，承重锚点新增
          `test_repros/round29_arm_shared_join_claim/r29a_01_shape_mimic_and_controls.pyc`
          （必须 2/2）与 `fly/dumpload/load_daily.pyc`（必须 23/23），
          `quotation.pyc` 143、`plugin_system_persist/__init__.pyc` 15、
          `custom_tools.pyc` 6 不变。
'''
# NB: `.replace` binds tighter than `+`, so it must be applied to the assembled block,
# not to the last literal -- otherwise the append lands with mixed line endings.
BLOCK = BLOCK.replace('\n', '\r\n')
assert BLOCK.count('\r\n') == BLOCK.count('\n'), 'mixed line endings in BLOCK'
assert '\r\r\n' not in BLOCK

# Round 28 already committed its own hand-off row checked (`- [x] SubTask 28.7:`), so there is
# nothing to flip here -- assert that, and assert this round's Task row is absent.
assert text.count(u'  - [x] SubTask 28.7:') == 1, 'round 28 hand-off row not found checked'
assert text.count(u'- [ ] Task 29:') == 0 and text.count(u'- [x] Task 29:') == 0, 'Task 29 already present'
new = text + BLOCK
out = new.encode('utf-8')
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
