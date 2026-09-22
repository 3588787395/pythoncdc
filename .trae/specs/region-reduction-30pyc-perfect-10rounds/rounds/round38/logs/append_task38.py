# -*- coding: utf-8 -*-
"""Byte-level append of Task 38 to tasks.md (Edit tool is forbidden for this file).

Asserts the exact current prefix identity (sha256/len/CRLF/LF-only counts) before writing, so a
stale read cannot double-append or truncate the user's ledger; then appends CRLF-normalised text
and re-asserts that the original bytes are an exact prefix of the result.

usage: python -X utf8 append_task38.py            # dry run: print what would be appended
       python -X utf8 append_task38.py --apply
"""
import hashlib
import io
import sys

SPEC = r'F:\Downloads\pythoncdc-main\.trae\specs\region-reduction-30pyc-perfect-10rounds'
T = SPEC + r'\tasks.md'
EXPECT_SHA20 = 'e732eb69ba66503b0d3a'
EXPECT_LEN = 183383
EXPECT_CRLF = 1712
EXPECT_LF_ONLY = 0

BODY = """- [x] Task 38: 零改动轮 —— 目标池重测 + 全 402 崩溃探针（带阳性对照）+ 靶簇形状拆分，
      三条线全部不达发货前置条件，`core/` 未写一字节（记录 `rounds/round38/arm-design.md` ＋
      `rounds/round38/OUTCOME.md`）
  - [x] SubTask 38.1: 靶轮字节确证 commit `7b8af974`、核 sha256[:20] `6b0759b1a0a566a4eb8f`
          （2 984 567 字节 / CRLF 48 421 / BOM 在位 / HEAD blob 与工作区逐字节全等 / `core/` 干净）；
          全部测量在该字节的私有镜像 `mirr_head` 上做，建臂后立即断言与工作区字节全等。
  - [x] SubTask 38.2: 目标池实测（`logs/pool38.py` 先断言 402 条全为 37 轮盖章、核 sha 未移动）：
          `files 402 partial 27 sum_deficit 96 deficit1 5 deficit2 11`；deficit-1／deficit-2 两池
          逐文件在 `head` 臂复测（`logs/g1head_d1_5.jsonl`、`logs/g1head_d2_11.jsonl`）与索引一致。
  - [x] SubTask 38.3: 先排除机械故障再谈判据 —— 全 402 崩溃探针 3 片（134 文件/片，0 error，
          33/32/54 秒）崩溃列全空；探针自身经反向 R36-A 镜像（`logs/spec_rev36a.json`）阳性对照，
          在 `fly_api/base.pyc` 复现 `2x TypeError @ :4824 in _fold_break_to_return`。
          ⇒ 96 个 deficit 函数全为判据级形状，语料内无被兜底吞掉的异常。
  - [x] SubTask 38.4: 形状聚类（`logs/sigscan38.py`，过滤后指令序列 difflib 对齐，签名=操作码序列＋
          删除操作码＋插入操作码）：81 组覆盖 94 个不匹配函数、0 未决；最大簇 8 个函数各差**一条**
          `JUMP_BACKWARD`。
  - [x] SubTask 38.5: 窗口探针 `logs/dupjump38.txt` **否证「一簇一形状」**，把 8 行拆成两族：
          子形状 A（2 行：前指令同 token、两回边同落点 ⇒ 重复回边并成一条，`continue` 被挪到
          if/elif 链外）与子形状 B（6 行：前指令不同、落点不同 ⇒ 臂尾回边被并掉、**else 臂摊平成
          顺序语句**，`fill_kline_data` 里 `=0` 随即被下一行覆盖 —— 产物语义错，不只是指令数错）。
  - [x] SubTask 38.6: 线 A（子形状 B）NOT-READY：自证其「把臂尾跳转从块名袋剥出来」的判据在区域
          构造期够不到（该层无「臂尾 vs 其他出口」概念）、点名站点实测未到达、建议的下一步实验未做。
  - [x] SubTask 38.7: 线 B（子形状 A）报告归因 `ast_from_stmt` elif 脱糖并给出「`orelse_if` 非空 ⇒
          忠实体」开关、点名 5 个构造站点 —— 编排方复核 `grep -n "def ast_from_stmt\\|orelse_if"
          core/cfg/region_ast_generator.py` ⇒ **0 命中**，函数与形参在核内均不存在，核内 elif 拼装在
          `:12427 / :15901 / :16012 / :32627` 一带以 `_is_elif` 标记。⇒ 判据不可按报告实施，不采纳。
  - [x] SubTask 38.8: 方法论收获（升级为采纳前置检查）：**代理报告里点名的每个函数名/形参名必须
          先 grep 验证存在**，行号必须与工作区字节对得上，才允许进入候选；本轮两条线各交了一份
          自洽但落不到字节上的方案，唯一拦住发货的是这条 grep（同族教训见 36.「探针没报 vs 探针坏了」）。
  - [x] SubTask 38.9: 编排方独立第三条线（`logs/fallback38.txt`）把 96 缺口里 8 行分三组：
          extra-jump 3（产物在原码直落处多插 `JUMP_FORWARD`，落点 498/420/346）、
          klinedata-return 2（原码「返回值语句＋跳共享清理尾巴」被就地展开成 `return`＋尾巴副本）、
          等长 `finally` 尾声换位 5。它们在官方尺上确为不匹配（`seq_len`/`seq_diff`），不是尺子噪声；
          但判据会压到 Round 33／35 刚落地的两条规则 ⇒ 不作本轮靶。
  - [x] SubTask 38.10: 门禁前置只做了一件有判别力的事 —— 子形状 A 的**不依赖语料的见证**已在落地
          字节上确证：`logs/g0_38.py` 于 `mirr_head` 跑 `logs/r38_elif_continue_controls.py` ⇒
          `DEFECT 1 1 ctl_two_cont:seq_-1`，其余三支 CLEAN；G0 驱动器自身冒烟通过
          （镜像解析断言、显式 `cfile`、异常钩子）。无候选判据 ⇒ G1–G7 无对象可跑。
  - [x] SubTask 38.11: 零改动的证明不靠自报：全 402 在 `head` 臂整批复测
          （`logs/g4_head.all.jsonl`，402 行 / 0 harness error）与 `pyc_index.json` 逐文件逐字段
          比对 **冲突 0**（`logs/index_vs_head38.py`），两侧同为 `Σtotal 5746 / Σmatched 5650 /
          整文件全匹配 375`；索引仍是 37 轮 G6 的实测回写，本轮未改写一个字段。
  - [x] SubTask 38.12: 移交 Round 39：①子形状 A —— 见证已就绪，改用线 A 未做的那步实验
          （打该 `if` 区域的 `then_blocks/else_blocks/merge` 与臂尾跳转）在核内真实符号体系里找站点，
          线 B 的 elif 假说须重新验证而非照抄；②子形状 B（6 行，产物语义错）先量「发射器是否本来
          就有臂尾表示」再定层；③§38.9 的 8 行三组；④未动的同簇兄弟 `matcher :: match 713/689`
          （机制 `region_analyzer.py:17290`，暴露面 21 函数／13 文件，R37-B 已 NO-GO）；
          ⑤台账继续在册：`clock_worker +6`、`decrypt_database_url 295/324 +29`（需放弃发射侧）、
          `events 510/508`（欠定，勿再从 else 归属侧进攻）、`_init_config 86/84`（R16 J1 反例，
          受保护勿再取）、`OverNightOrder.__init__ 172/148 −24`、#61 汇合块残余 +
          `r29x_01 <module> 142/138`、`:2118` 一带未读的 `orelse` 消费方；⑥门禁基线已在镜像测好，
          下一轮只需跑改后侧：G2′ `logs/reprobat59.txt` ← `logs/g2p_head59.jsonl`（59/48/Σ|Δ|176）、
          G3 `logs/anchors107.txt` ← `logs/g3_head107.jsonl`（107/77/Σ|Δ|446）、
          G4 改前侧 `logs/g4_head.all.jsonl`。
"""

raw = io.open(T, 'rb').read()
assert hashlib.sha256(raw).hexdigest()[:20] == EXPECT_SHA20, 'prefix sha moved'
assert len(raw) == EXPECT_LEN and raw.count(b'\r\n') == EXPECT_CRLF \
    and raw.count(b'\n') - raw.count(b'\r\n') == EXPECT_LF_ONLY, 'prefix byte profile moved'

add = BODY.replace('\n', '\r\n').encode('utf-8')
out = raw + add
assert out[:len(raw)] == raw and len(out) == len(raw) + len(add)
print('prefix verified  sha20 %s len %d  ->  new len %d (+%d bytes, %d lines)'
      % (EXPECT_SHA20, len(raw), len(out), len(add), BODY.count('\n')))
if '--apply' in sys.argv:
    io.open(T, 'wb').write(out)
    b2 = io.open(T, 'rb').read()
    assert b2 == out and hashlib.sha256(b2).hexdigest()[:20] != EXPECT_SHA20
    assert b2.count(b'\n') - b2.count(b'\r\n') == 0, 'LF-only leaked in'
    print('written  sha20 %s len %d CRLF %d' % (hashlib.sha256(b2).hexdigest()[:20],
                                                len(b2), b2.count(b'\r\n')))
