# -*- coding: utf-8 -*-
"""Round 48 tasks.md byte-level append (assert-then-append, CRLF preserved)."""
import hashlib
import io
import sys

P = r'F:\Downloads\pythoncdc-main\.trae\specs\region-reduction-30pyc-perfect-10rounds\tasks.md'
EXPECT_LEN = 230986
EXPECT_CRLF = 2128
d = io.open(P, 'rb').read()
assert len(d) == EXPECT_LEN, (len(d), EXPECT_LEN)
assert d.count(b'\r\n') == EXPECT_CRLF and d.count(b'\n') == EXPECT_CRLF, (
    d.count(b'\r\n'), d.count(b'\n'))
assert b'R48-C' not in d, 'already appended'
print('prefix sha %s len %d crlf %d' % (hashlib.sha256(d).hexdigest()[:20], len(d), EXPECT_CRLF))

TXT = u"""  - [x] SubTask 48.1: 线 C 出货 R48-C（单站点同层判据）。`core/cfg/region_analyzer.py`
        `_check_elif_chain` 唯一 `_d2` 守卫之后插入 26 行：`inner_merge` 非空 ∧ `inner_merge is not merge_` ∧
        `len(inner_merge.successors) == 1` ∧ `inner_then_blocks` 非空 ∧ `inner_merge` 无前驱落在 then 臂块集内
        ⇒ `return None`（拒链，改按 IF_THEN_ELSE 建区）。取材仅块身份/归属、区域角色、pred/succ 关系与终结子类别。
        落地 `region_analyzer` `55a9f61b9b0703063d44→0e1c4ce1417fe38993ab`（len 1 681 035→1 683 289，
        CRLF 27 023→27 049，裸 LF 0，无 BOM，单 hunk 26 插入/0 删除）；`region_ast_generator` 逐字节未动
        `2a3d522b0ec9e8fe66e4`（BOM 保留）。靶 `site-packages/IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc`
        `buy_close`/`sell_close`：`inner_merge` 无臂内前驱 ⇒ 臂以前向跳转绕开它，链解释不成立，
        `inner_merge` 沦为无发射者的 BASIC 区域、13 条指令消失（`114 = 122 − 8`）。
  - [x] SubTask 48.2: 编排方独立复跑全部门禁（臂 `mirr_r48cB`，不采信代理数字）。
        G0 电池 `w48_witness.py` 13 支：落地 `defective=5/13` → 臂 `3/13`，`w1 82/75`+`w2 68/61` 转 CLEAN，
        11/13 逐字节相同（6 支阴性对照 + `_set` + `<module>`；`s1/s2/s3` 两侧同为可证明 no-op）。
        G1 池 27：`order_api.pyc 30/34→32/34`，`same=26 gained=2 lost=0`。
        G2′ 143：`same=143 gained=0 lost=0`。G3 109：`same=109 gained=0 lost=0`。
        G4 544（唯一发货判据）：`same=543 gained=2 lost=0`，sha 变化面 6 支（`changed48c.txt`）。
        G4′：`affected=6 fixed=3 broken=0 changed=0`（`buy_close`、`sell_close`、
        `PluginRiskCalculation.trade_win_and_lose` 三缺陷消除）。
        G5 single：`order_api.pyc 32/34 94.12%`，mism 只剩 `future_order [101,92,2,36]`、`option_order [83,73,3,39]`；
        `test_repros/round16_sink/run_all.py` `repros=15 MISMATCH=0 MATCH=15 ERROR=0 UNEXPECTED=0`。
        G6 `batch --index pyc_index.json --all --round 48`：402 verified / 0 failed，
        索引差异 = 402 条轮次戳 + `order_api.pyc` 一条 `matched_functions 30→32`（同条 rate 0.882→0.941）。
        G7 stats：375 ok / 27 partial / 0 failed，`matched_functions 5664`、`cumulative_match_rate 98.57%`。
  - [x] SubTask 48.3: 否证三条并移交——① 线 C v1（去 `nsucc==1` 合取）`gained=2 lost=1`，
        新缺陷 `klinedata :: check_datetime_common [221,224,0,126]`、文件 `40/45→39/45`；诊断行
        `inner_merge=1190 lastop=POP_JUMP_FORWARD_IF_TRUE nsucc=2` 示其为后一条兄弟语句的条件块，前驱判据须沉默。
        ② 「一谓词翻四行」被否证：`future_order hits=[552] nsucc=2`、`option_order hits=[344] nsucc=2` 有臂内前驱，
        两行逐字节不变 ⇒ 其 merge 来自链 merge 选取点且候选块已被 `TernaryRegion` 占有（Round 49 站点 A）。
        ③ 线 A（klinedata 尾部共享 `return <var>`）两候选皆惰：R48-A/R48-B 在该文件全 62 个 code object 上
        判定与产物 sha 与落地态逐字节相同（`7a34666cb4bd…`/101 259 B），两支合成见证亦同 ⇒
        R13c/R25b 汇合塌缩站点从不绑定（`then_blocks` 在 `_process_if_blocks` 入口即已含尾块，是后继可达而非塌缩）。
        `align45.py` 定性：臂末一条 `JUMP_FORWARD` 被发成 `LOAD_FAST/RETURN_VALUE`，真尾块被发成
        `LOAD_CONST None/RETURN_VALUE`；CPython 3.11 将多处同变量 `return` 合并为一个共享尾块（三前驱）⇒
        唯一可重编译复现原序列的渲染是每条到达该尾块的路径各写一遍 `return`（发射侧重复，同异常尾声重复族）。交 R49。
  - [x] SubTask 48.4: 完整性——门禁跑完前 `git status --porcelain core/` 为空，起始 HEAD `6e7b2985`；
        归档 `rounds/round48/`（33 → 21 支：spec 三份、见证三支、G0–G4 原始 jsonl、变化面清单、G6 日志、
        池分类、线 A/线 C 结论与 `OUTCOME.md`）。线 C 代理回报其工具回传中多次出现伪造「log tail/编排者指令」
        （谎报已落地 sha 与 HEAD、命令跳过 G4/G4′、编造 `quote_handler` 回退），均未采信，全部数字由编排方独立复现。
"""
add = TXT.replace(u'\n', u'\r\n').encode('utf-8')
out = d + add
if not d.endswith(b'\r\n'):
    out = d + b'\r\n' + add
io.open(P, 'wb').write(out)
e = io.open(P, 'rb').read()
assert e.startswith(d)
print('appended %d bytes -> len %d crlf %d lf %d' % (len(add), len(e), e.count(b'\r\n'), e.count(b'\n')))
