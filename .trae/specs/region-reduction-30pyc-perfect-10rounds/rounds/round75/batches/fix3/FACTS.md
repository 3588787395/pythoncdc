# Round75 fix3 修复批 —— inside-try 9 单元（BRIEF_fix3）

- 工作区 `D:/Temp/opencode/r75gate/fix3`；基线 HEAD `982cd398`（fix1/fix2 均未落地，本批臂全部对落地核反打）。
- 除本归档外 repo 零写入（G0 `git status core/ scripts/ site-packages/` 已跟踪零改动）、不手改 `*OK.py`、未跑落地。
- **最终臂 = `abdef`**（`specs/trym.json` 与 `tmp/abdef.json` 内容逐字相同，即 BRIEF 要求的合并臂 `trym`）：
  5 edits 全在 `core/cfg/region_analyzer.py`，`+218` 行、1 781 244 → 1 798 170 B，
  = or 链首段极性补齐 **A**（or1）+ 正常流汇点守卫 **B2**（sink1）+ elif 链收尾 **D**（chf1）
  + 链内发射 **E**（e1）+ 兜底 merge 终版 **F**（f1，含四段收窄）。
- 工程注：任务书写的 `mbuild75.py` 未存在，实际用 `center/mbuild74.py <arm> <spec.json>`（锚点断言全过）；
  单臂矩阵、探针、门禁命令见 `scripts/`。

## 1. mandate

| 判据 | 读数 |
|---|---|
| `IQData/…/real_quote.pyc` | landed `43/45 failure` → **abdef `45/45 success`**（mandate 达成） |
| h62 单元级 | `get_real_minute_kline [253,254,3,197]`、`get_tick_direction [259,258,3,102]` 两条 better |

## 2. 门禁（a–e 全部对最终臂 fresh 复跑）

| 项 | 读数 | 判定 |
|---|---|---|
| a 官方 41 靶 `h62 run --arm=abdef --list=list41.txt` vs `list41_land2` | **REGRESSION=0**；差异面 8 文件：SHA-ONLY `klinedata`/`finance`/`trade_live_broker`，better `real_quote 42→44`、`quote 72→73`，`realtime_event_source 11/12` 持平（clock_worker 见 §5 MOVED 裁定） | PASS |
| a′ 官方 402 全量 vs `p402_landed` | **REGRESSION=0**；SHA-ONLY 7（+`tools`/`history_data_source`/`order_api_trade`/`scheduler`/`pboxAccount_jupyterhub`）+ 同上 3 支变化 | PASS |
| b mandated focus `mand_ab.py` | **CLEARED=0 NEW=4**（`run_tick_socket`、`get_real_minute_kline`、`get_tick_direction`、`get_fields`）；无任何单元新生失败 | PASS |
| b′ 逐支 `pyc_verify single` | real_quote **45/45 success**；`finance 32/32`（landed 31/32）；`quote 82/92`（landed 81/92）；`wizard 55/58`、`load_daily 26/27`、`risk_calculation 41/43`、`time_validator 5/5`、`trade_info_utils 36/41` **全部 = landed** | PASS |
| c 金丝雀 4 支 | `quotation 3eb76e512df9ab1e`、`market_time af77224b34b203c4`、`datetime_func e711b8ea86d49a15`、`IQData/datetime_func 9d09af09249da177` —— 4/4 sha16 == pin | PASS |
| d 电池 `closeout69.py battery abdef` | `candidate columns worse-than-landed on 0 repro(s)` | PASS |
| e 严格尺 `sstrict67 build_abdef vs build_landed list41` | ok `1649 → 1653 / 1718`、defects `69 → 65`；**新增缺陷函数 0**（唯一 NEW 行是 `clock_worker` 同函数 seq_len 数值位移 1286→1189，ADR-1 判 IMPROVED），CLEARED 5 行（finance 1、real_quote 2、realtime 1、quote 1） | PASS |
| 附加 ADR-1 `adr73 abdef fam75.json` | units 71 changed 5 **WORSE=0 IMPROVED=5**（finance.get_fields hunk1→0、real_quote×2、clock_worker sd760→744、quote.run_tick_socket hunk11→0） | PASS |
| G0 `scripts/g0audit.py` | **11/11 PASS**（三要素注释、无 self 状态/`getattr(self..)`、无跨层 `X.entry in Y.blocks`、无文件名/靶函数名白名单、无 `start_offset` 阈值、反打 ast+py_compile、BOM 同原件、repo 零写入） | PASS |
| synth | 见 §6：**SYNTH PASS**（复现翻转 + 负例逐字节同） | PASS |

## 3. 9 个 inside-try 单元判定（BRIEF §1/§2，三选一根因 = a 共享尾在 try 内被吸收 / b handler 出口错位 / c try 内 boolop/elif 链归约）

| 单元 | 本批读数 | 根因判定（证据） |
|---|---|---|
| `real_quote :: get_real_minute_kline`（IN，et=7） | **修绿**：pbv 43/45→45/45，h62 better | **(c)**：`if fq is None or ex_info is None` 首段 opcode 为 `IF_NONE`，原 or 链守卫只放 `IF_TRUE/IF_FALSE` ⇒ 链退化为 `if not A:` 反转+嵌套（A 的 G0 注释即此）；A 放行 `IF_NONE` 后链正确重定向 |
| `real_quote :: get_tick_direction`（OUT，R74 拒收点） | **修绿**（随同一链；h62 better，ADR hunk 12→0） | **(c)** 同链；与 IN 单元同 region 链，修复未触发 `hunks_norm 2→3`（ADR WORSE=0） |
| `finance :: get_fields`（F-ABSORB，et=8） | **修绿**：文件 31/32→**32/32 success**，strict 该文件缺陷 1→0 | **(c)**：landed 把 `elif table in …` 渲染错层，链归约修正后 hunk 1→0 |
| `quote :: run_tick_socket`（F-PAD，et=13） | **改善未全绿**：pbv 81→82/92，h62 better，ADR hunk 11→0 sd 248→0 | **(c)/F-PAD 重叠**：pad 差异由链收尾 D/E 消去，剩余失败单元不在本批判据面 |
| `realtime_event_source :: clock_worker`（F-ABSORB，et=24） | **位移**：h62 `[1275,1285,10,481]→[1275,1188,10,471]`（同 11/12），ADR hunk 52→49 sd 760→744 **IMPROVED** | **(c)** 部分：改写确实动了该单元；按 ADR-1（hunks/sd 双降）判改善而非回退，裁定见 §5 |
| `trade_info_utils :: trade_operation`（et=18，R70 #94） | 未动：36/41 两臂同态 | 根因不在本批判据面（fix2 的 E 规则已单臂清过该单元但 fix2 未落地；本批按硬规不自合并他批 spec） |
| `email_utils :: send_email`（et=5） | 未动：3/4 两臂同态 | 未覆盖（首分歧在 handler 出口族，(b) 候选，本轮无该路径判据） |
| `cgroup_utils :: set_cgroup_config` | 未动：7/8 两臂同态 | 未覆盖 |
| `flytools :: modify_batcktes_info`（F-PAD，et=22） | 未动：65/66 两臂同态 | fix2 已判 (iii) 纯位移（Δ24），非本批 |
| `strategy :: tick_worker_thread` | 未动：26/27 两臂同态 | diag1 Q2：异常表字节全同 ⇒ try=载体，根因在 try 内区域归约但不属本批链判据 |

**et/首分歧口径**：本批 5 条编辑全部在 `region_analyzer` 分析层，改的是链/汇点区域的归约与 merge 选择，
不新增 try 层、不动发射层 —— 所以 et（异常表条目数）读数不变，变化的是 try **内部**的链结构渲染；
首分歧在区外的单元（对照组）读数自然不变，与 diag1 Q4「载体 3 / 并列 4、intry=0」一致。
**对照组解释**：`et>0` 但首分歧区外 = try 只是载体（异常表字节全同）或判据口径差，本批不修这些单元即零回退。

## 4. F（兜底 merge）判据取证与四段收窄（本批核心方法论）

F 的原始问题（fix3 前半程定位）：`if (merge is None and _main_inline_boolop_chain is not None)` 兜底把
merge 落到 `else_succ`，当 or 链两臂都是终点臂时 `else_blocks` 归空、链区退化 IF_THEN，else 臂块既不在
链区 blocks 也不在父 elif 链的 body 列表 ⇒ 掉函数末尾孤儿兜底（wizard `filter_desicion` 的
`return up_v_desicion(...)` 挪到整条 if-elif 链之后、字节码缺 3 条即此形态）。

| 版本 | 判据 | 结果（可复现读数） |
|---|---|---|
| F-v1 无门 | else 臂 sink 即跳过兜底 | `load_daily` 丢 `return (None,-1)`（and 链共享尾被 merge=None 后经 R71 gap 吞并） ⇒ 拒收 |
| F-v2 `[收窄]` | + `op=='or'` | 41 REG=0；402 出 **3 REG**：`history_data_source 18→15`、`time_validator.can_cancel_order 5→4`、`custom_tools 5→6?→5`（fsink 站点全 op=or；`abde` 臂 402 只有 wizard REG ⇒ 三者归因 F；R71 在三文件零触发 ⇒ 是结构改变本身） |
| F-v3 `[收窄-2]` | + then 臂无正常后继（终点臂） | 41+402 双 REG=0；但 mand 出 **CLEARED=1**：`risk_calculation.next_day 41/43→40/43`（顶层层 `if not A or B:`，merge=else_succ 本来就对） |
| F-v4 `[收窄-3]` | + 本块有条件跳转前驱（顶层 if 排除） | next_day 恢复 41/43、mand CLEARED=0；但合成 s2 形态 `if not A or B: return 1 else: return 2`（单局外层 if/else）被渲成语义错 ⇒ 判据仍不够 |
| F-v5 `[收窄-4]`（**终版**） | + 祖先链上溯存在链证据（某祖先条件块的其他后继也是条件块 = elif 链续接） | s2 恢复 success、wizard h62 SAME、41/402 双 REG=0、全套门禁绿（即本归档臂） |

判据全部只读同层结构事实（块末指令 opcode、后继/前驱集合、异常边、`_main_inline_boolop_chain.op`），
无函数名/文件名/偏移阈值/名字白名单/新增 self 状态/跨层 `region.entry in r.blocks`（G0 11/11 证）。
单臂归因：`or1` 单独造成 wizard h62 REG=1（A 的 IF_NONE 放行在链内触发重定向）、`sink1/xp1/chf1/e1` 全 SAME、
`abde`（A+B+D+E 无 F）wizard REG=1、`abdef`（+F 终版）wizard SAME ⇒ F 的语料内净作用 = 抵消 A 在链内的
几何位移，使链内渲染回到与落地逐字节一致（wizard 两臂产物 `Compare-Object` 为空）。

## 5. MOVED 裁定（交中心）

`realtime_event_source :: clock_worker`：h62 计数 11/12 不变、mism 行从 `[1275,1285,10,481]` 移到
`[1275,1188,10,471]`；严格尺同函数 seq_len `decomp 1286→1189`（仍是缺陷行）；**ADR-1 该单元 hunk 52→49、
sd 760→744 双降判 IMPROVED**。建议按 ADR-1 记改善、下轮基线以本臂重导，不作回退。

## 6. synth（BRIEF §3 synth 项）

- **复现 `repro75_f3_orchain`（t2）= 「try 内共享尾」最小复现**：or-is-None 链在 try 体内、try 尾带共享
  except —— `landed failure 1/2` → `abdef success 2/2`，两臂 sha 不同
  （同形状去掉 try 的 t1/t3/t4/t5 两臂均 success ⇒ **try 共享尾正是触发条件**，与 Q2 条目数差读数同源）。
- **负例 `neg75_f3_nested` = 真嵌套 try**（try 内再 try、两层 handler）：两臂 sha `8dd91599288d1304`
  **逐字节相同**、两侧均 3/3 success。
- `out/synth.json` verdict 5/5 true ⇒ `SYNTH PASS`。

## 7. 与 fix1/fix2 重叠面

- 与 **fix1**（`_cjb_skip_inline_if` 丢前导操作数，jq 2 单元）：0 单元交集，本批无该路径改写。
- 与 **fix2**（try 尾 break 桩 E、D2′ 纯度、grp_g/C9/D/pad8_1f，`ec_ge`+`ad5b` 两 spec）：
  同文件 `region_analyzer` 但锚点互不相交（fix2 的 ad5b 4 edits vs 本批 5 edits，merge 反打断言均 count==1）；
  单元面重合 `run_tick_socket`/`modify_batcktes_info` 两处 IN 靶 —— 本批只改善前者、后者未动，
  **不自合并他批 spec**（`trade_operation` 等 fix2 已清单元因此仍 36/41，属预期）。
- 与 **diag1**：本批即 diag1 交接的「(c) 族 + MERGEABS/链守卫」方向；F 的四段收窄是 diag1 A∩B「改守卫
  须同批回归 orphan」教训的直接落地（每加一段门就复跑 41+402+mand）。

## 8. 已知边界（如实记录）

- 合成 s2 形态（or 链 + 两臂终点 + **单局外层 if/else 无链证据**）在 F-v3/v4 下被渲成语义错（`if not b or c`
  的 else 臂挂进内层），v5 已修；402 全量无该形态 REG ⇒ 语料内零命中。
- `strict` 唯一 NEW 行为同函数数值位移（§5），按缺陷函数计 NEW=0。
- 本批臂未含 fix1/fix2 spec（未落地基线），跨批叠加并集交中心后续 `land*` 流程处理。

## 9. 交付清单

- `FACTS.md`（本文件）
- `specs/`：`or1 / sink1 / xp1 / chf1 / e1 / f1`（单臂）+ `trym.json`（合并臂，5 edits）+ `abdef.json`（= `trym.json`，来源 `tmp/abdef.json` 逐字相同）
- `scripts/`：`mkspecs.py`（spec 生成器，含三要素注释与四段收窄）、`merge.py`、`ab2.py`（h62 jsonl 差分）、
  `g0audit.py`（G0 11 项）、`preds.py`/`ctx.py`/`sinkprobe.py`/`reach.py`（F 判据探针）、
  `_p8/_p9/_p10/_p11.py`（收窄迭代补丁，逐版可回放）
- `synth/`：`build_synth.py`、`repro75_f3_orchain.py`、`neg75_f3_nested.py`（.pyc 按批惯例不入库，`build_synth.py`
  可再生成）、`probe_synth.py`/`probe_t.py`（形状探针）、`out/synth.json`
- `dump/`：门禁原始读数（`list41_{land2,abdef,abde,or1,sink1,chf1,e1,xp1,exp4,exp6,exp7,exp8,exp10}.jsonl`、
  `p402_{abdef_f,abde,exp7,exp8,exp10}.jsonl`、`wiz_*.jsonl`、`canary_abdef.jsonl`、
  `mand_abdef41_f.json`、`strict_{landed,abdef}41.json`、`g0audit.txt`、`gates75_fix3.txt`（§2 汇总）、
  `battery_landed_vs_abdef.txt`、`adr74_abdef.json`、`fsink.log`（F 站点 or/and 普查，`git add -f`）、
  `r71_land.log`（R71 归因，`git add -f`）、`list_wiz.txt`、区域/站点取证 `bk_*`/`gtd_*`/`rqk_*`/`or1_dbg.txt`）
