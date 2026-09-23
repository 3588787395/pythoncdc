# -*- coding: utf-8 -*-
"""Append Round 50 SubTasks to tasks.md byte-exactly (prefix sha/len/CRLF asserted first)."""
import hashlib
import io

P = (r'F:/Downloads/pythoncdc-main/.trae/specs/'
     'region-reduction-30pyc-perfect-10rounds/tasks.md')

raw = io.open(P, 'rb').read()
pre_len = len(raw)
pre_sha = hashlib.sha256(raw).hexdigest()[:20]
pre_crlf = raw.count(b'\r\n')
pre_lf = raw.count(b'\n')
print('before len=%d sha20=%s crlf=%d lf=%d' % (pre_len, pre_sha, pre_crlf, pre_lf))
assert pre_crlf == pre_lf, 'tasks.md has bare LF lines before append'

L = [
    '  - [x] SubTask 50.1: 接手 Round 49 移交的链 merge 线并把靶子钉在 `order_api.pyc :: '
    '\r\n          future_order/option_order`（落地 strict `33/36`：`base_order [target_diff] #136`、'
    '\r\n          `future_order [seq_len] 101/93`、`option_order [seq_len] 83/74`）。带打印镜像核实测：'
    '\r\n          `_identify_conditional_regions` 对 `H=130 T=174 E=178` 留 `merge=None`（then 臂 `RETURN_VALUE` '
    '\r\n          且无正常流后继、`else_succ` 前驱仅 `[130]`、`_else_sink` 因 ipdom 链触到函数尾 return 而被误置真），'
    '\r\n          随后 `_build_elif_region` 链兜底把下一条语句的条件头 `178` 当 elif 条件、把 `TernaryRegion@206` '
    '\r\n          的两臂块 `344/348` 当 body/final_else，取共同后继 `350` 作 merge'
    '\r\n          （`conds=[178] bodies=[[344]] fe=[348] exits=[[],[350],[350]] cands=[350]`）。',
    '\r\n  - [x] SubTask 50.2: 三条候选判据全部 G0 否证（6 真 pyc ＋合成电池，编排方独立复跑）：'
    '\r\n          `r50a`（17062 区段早站点五条合取改绑 `merge=else_succ`）order_api `33/36→34/36` 但'
    '\r\n          `future/option` 发射 `93/74→77/65`、`quotation.pyc 148/150→134/150`、'
    '\r\n          `quote_handler :: get_index_stocks_local 150→60` ⇒ 绕过 `IF_ELIF_CHAIN` 与 R33/R35 兜底的全局外溢；'
    '\r\n          `r50b`（19441–19452 链候选剔除 `TernaryRegion` 已认领块）**确实开火**（`cands=[350]→[]`，'
    '\r\n          `owned=[206,344,348,350,418,422,424,504,508,510]`）而产物逐字节同落地 ⇒ 惰；'
    '\r\n          `r50e`（早站点 ＋ 第⑥合取「`else_succ` 的后继是某 `TernaryRegion` 入口」）`PRED=True` 命中且'
    '\r\n          把 `option_order` 形状从 `elif is_trade() or ...: pass / else: """卖出"""` 纠正为 `if not is_trade():`，'
    '\r\n          但 strict 反而 `74→65`（整条 `Expr(Call)` 被整段丢掉）⇒ 否证原命题。',
    '\r\n  - [x] SubTask 50.3: 真实根因改判到生成器侧并逐行取证：`region_ast_generator.py` '
    '\r\n          `_try_build_ternary_kwarg_call`（定义 41375、唯一调用点 36829）在 41500–41505 的 kwarg 槽位装配'
    '\r\n          循环 `return None`，臂内打印两条 bail：`preload_kwarg i=1 names=(\'order_id\',\'symbol\',\'side\','
    '\r\n          \'oper\',\'share\',\'hedge_type\') n_tern=1 entry=424`（option_order）与 `... i=1 n_tern=1 entry=558`'
    '\r\n          （future_order）。两处独立缺口：①41464/41501 只支持「三元链结果连续占据 kwargs 前若干槽」，'
    '\r\n          注释自认 `# Would need preload kwarg value — not in R9 cases.`；②链行走 41400–41412 只沿 '
    '\r\n          `region.merge_block == inner.entry` **前向**延伸，故传进来的 region 已是链尾（424/558），'
    '\r\n          链头 `206`、`350` 与其间的并列值（`order_.order_id`/`order_.symbol`/`order_.amount`）无从装配 '
    '\r\n          ⇒ 真源那条 `strategy_log.info(\'...\'.format(6 个 kwargs，其中 3 个是三元))` 只剩碎片，'
    '\r\n          `LOAD_METHOD`＋`CALL` 被错绑成 `hedge_type.value.upper(<三元>)`。',
    '\r\n  - [x] SubTask 50.4: 旁支否证一并入册以免重走：R49-A 扩展线（把 `_r49a_shared_sink_tail_merge` 挂到其余 '
    '\r\n          `merge = else_succ` 绑定点）对 `klinedata :: _all_bars_of_cache`、`kline_datetime_list` 的所有 if '
    '\r\n          区域实测 `cands=[]`，`get_multiminute_his_data` 唯一命中（`H=718→2758`）改绑前后 merge 相同 '
    '\r\n          ⇒ 该三支残余非此形状；诚实覆盖边界：自建见证 `r50_target_shape :: shape_exit_then_ternary_stmt` '
    '\r\n          落地 `orig=28 decomp=31`、`r50a/r50e` 均为 `26`（方向相反），因语料那条语句是「三三元＋三并列值」'
    '\r\n          而见证只有一个三元 ⇒ 下一轮的见证须按 6 kwargs 重建。',
    '\r\n  - [x] SubTask 50.5: 收口＝**core/ 零改动、不发货**：`region_analyzer.py` 逐字节仍为 '
    '\r\n          `c644a6ccab745ac6be0e` / 1 687 755 B / CRLF 27 126 / 裸 LF 0 / 无 BOM（＝Round 49 落地态），'
    '\r\n          `region_ast_generator.py` 未动（BOM 保留），`git status --porcelain core/ pycdc.py` 空；'
    '\r\n          未跑 G1–G7、未改 `pyc_index.json`，官方尺数字仍为 Round 49 收口那一份。'
    '\r\n          移交 Round 51 线 A（两点分别开证）：入口 region 须取语句最外层三元（靶子 `entry=206`）；'
    '\r\n          kwarg 槽位逐槽判定「三元结果 / 该步 merge 块上的值」并取消 41501 早退。'
    '\r\n          同文件第三支 `base_order [target_diff] #136` 是不同形状（跳转终点常量错位），不得并入同一判据。'
    '\r\n          归档 `rounds/round50/`：`OUTCOME.md` ＋ `measure50.txt`（strict 表·链诊断·bail 打印·产物差异）'
    '\r\n          ＋三臂 spec 与脚本 ＋ `wit50/`。',
]

body = ''.join(L)
if not body.endswith('\r\n'):
    body += '\r\n'
io.open(P, 'ab').write(body.encode('utf-8'))

raw2 = io.open(P, 'rb').read()
print('after  len=%d sha20=%s crlf=%d lf=%d added=%d' % (
    len(raw2), hashlib.sha256(raw2).hexdigest()[:20],
    raw2.count(b'\r\n'), raw2.count(b'\n'), len(raw2) - pre_len))
assert raw2[:pre_len] == raw, 'append mutated prefix'
assert raw2.count(b'\r\n') == raw2.count(b'\n'), 'append introduced bare LF'
