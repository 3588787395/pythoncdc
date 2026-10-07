# Round 8 主代理验证序（VERIFICATION）

轮次：rr-v3r08 · Task 9
封表时点：2026-10-07（判据唯一 `scripts/pyc_verify.py`，ruler sha `9c7567bd6776b36b`，3.11.7 64 位）
before = `baseline/shards/shard*_report.json`（6554/6617、369/402）与 `rounds/round7/after/`（6574/6617、383/402）
after  = `rounds/round8/after/shard*_report.json`（402 产物全部先删后由 `pycdc.py` 重生成，ok=402 bad=0；8 片 verify 全 rc=0）
留证    = `rounds/round8/after_preG7_b121_only/`（B121 未加 G7 时的八片读数，即抓到回退的那一轮，不覆盖不销毁）

## I. 验证序读数（六步，串行单链）

| # | 步骤 | 读数 | 判定 |
|---|------|------|------|
| 0 | 402 产物重生成 | `regen_list.py` 231s，ok=402 bad=0；无一失败 | ✓ |
| 1 | 34 小测试集 batch | 1526/1568（97.32%）、失败 18 文件——名单全部落在语料残局内，`history_data_source` 已不在其中 | ✓ 零新增 |
| 2 | 402 八分片 + 双向 compare | units 6554→**6575/6617（99.3653%）**、files 369→**384/402**、compile_error 0、error 0 | **REGRESSIONS=0 ∧ UNIT_REGRESSIONS=0** ✓ |
| 2b | 对 Round 7 终态 | units 6574→**6575**、files 383→**384**（NEW-OK = `fly/common/flytools`）；unit_down=0 file_down=0 | 双向零回退 ✓ |
| 3 | quotation 锚点 | 重生成后 **153/153 success**；`quote_handler` 79/79、`ptradeAccount` 137/137 | ✓ |
| 4 | tests 六套件 | **2 failed / 277 passed / 2 xpassed**（仍 `test_B01_simple_if_then_else_merge`、`test_BOUNDARY_02_large_function`＝基线那二条） | ✓ 零新增失败 |
| 5 | 电池（主代理复算，292 臂产物全部先删后重生成） | `r1` 108/110、`r1_regress` 34/34、`r2v3` 105/126、`r3` 101/122、`r4` **79/87**（R7 为 77/87，+2）、`r6` 76/85、`r8` **56/62**（29→31 臂） | 零绿臂转红 ✓ |
| 6 | IV.2 门禁自检 | IMPORT_OK×3、compileall rc=0、`check_patch_patterns.py` PASS（禁止前缀 0）、BOM 单头 efbbbf + 全 CRLF（58985/58985）、探针脚本只在 `D:/Temp/rrv8` | ✓ |

## II. 本轮落地：B121 sinkarms + G7（两击，第二击纠第一击的回退）

**第一击（`[R8-B121 sinkarms]`，修复工程师）**：隐式 `return None` 的**逐边落点块**不再当语句发射。
判据 G1–G6（同图内无汇合 return 块 / 终块单前驱 / pure-none 或 handler-teardown 两形 / 转移边身份 /
G4b 条件测试的顺序落点不算出口 / 前驱与落点同属一区域 / 不在 `_with_jump_exit_blocks`），全有或全无。
实测把 `flytools.modify_batcktes_info` 的 6 个落点块（722/748/906/918/930/942）识别为一集，
`flytools` 65/66 → **66/66**，`quote` 86→87，`r4` 电池 +2。

**门禁抓到的回退（主代理全量门禁，工单未报）**：`history_data_source.get_bars` 19/19 → **18/19**
（success → failure）。探针 `D:/Temp/rrv8/probe_b121_roles.py` 实测：off288/off292 同为 pure-none、
同单前驱、同由条件测试假边跳转接入，G1–G6 全过——但它们是 `IfRegion@218.else_blocks` 与
`IfRegion@0.else_blocks` 的**唯一成员**，即源码写下的 `else: return None` 两条真语句。
⇒ 工单理论里「显式 return None 必产生汇合块（前驱 ≥2）」这一前提是错的：
单独的 `else: return None` 产出的正是**单前驱 pure-none 块**，与逐边内联副本在 CFG 形状上不可分。

**第二击（G7，主代理落地）**：能区分的不是边的身份，而是「该尾是否由前驱那条已发射语句自身的
退出路径携带」——块为 'handler-epilogue'（退栈对就在本块内），或前驱块末 opcode 为 `POP_TOP`
（with `__exit__` 结果丢弃 / 调用值丢弃后的顺序续体）。这是块级 opcode 事实，不取宿主类型、
不取深度、不取计数。落地后：`get_bars` 判据集合为空（两块照常发射、19/19 复绿），
`flytools` 集合不变（6 块仍抑制、66/66 保持）。G7 之后再跑一次全量门禁，即上表读数。

`quote` 相对 preG7 让回 1 单元（87→86），但相对 Round 7 不回退（86→86，仍 −6）：
G7 把 B121 在 `quote` 里对 pure-none 假边落点的那一次过度吞并纠正回来了。

## III. 主代理独立取证（不采信工单自述）

1. **产物溯源**：14 个目标产物（`flytools`/`quote` + 6 条 `r8nop` + 6 条 `r8b121` 臂）用当前字节重生成后
   与落盘件 sha256 前 16 位**逐位相等**（DIFF_COUNT=0）⇒ 读数出自发射器，非手改。
2. **判据可复现**：`single flytools` 66/66、`single quotation` 153/153 由主代理亲跑重生成+判定，非引用工单数字。
3. **电池口径**：七套 292 个臂产物一律先删后重生成再判，G7 前后读数逐批相等。
4. **陈旧读数防线**：`cmd_verify` 先删同名旧报告；本轮 8 片全部新产出，无陈旧读数混入。
5. **未登记标本纠处**：工单留下 `r8b121_02_with_body_and_arms` 与 `r8b121_03_two_handlers` 两条
   改名后的孤儿标本（不在索引＝第二真相源风险）。实测与已登记同编号标本**形状不同**（前者无 if 臂、
   后者为 while+try+双 handler），故选择**登记入索引**（29→31）而非删除；`site-packages/IQCommon/util/email_utils.pyOK.py`
   （0 字节、由畸形 `email_utils.py.pyc` 派生）删除。

## IV. 轮门禁判定

- ≥1 个 pyc 由 failure 转 success：**1 个**（`site-packages/fly/common/flytools.pyc` 66/66，同目录 `+OK.py` 全单元 Equal）✓
- 全量单元读数净增：6574 → **6575**（对基线 +21）；files 383 → **384** ✓
- 双向零回退（对基线、对 Round 7）：unit_down=0、file_down=0 ✓
- 语料残局：**18 文件 / 42 单元**（Round 7 为 19 / 43）
  −10 `trade_live_broker`、−6 `quote`、−4 `trade_info_utils`、−3 `klinedata`、−3 `wizard_quant_api`、
  −2 `real_quote`、−2 `order_api`、−2 `risk_calculation/__init__`、
  −1 `finance` `handlers` `api_base` `bar` `strategy_universe` `strategy` `realtime_event_source` `matcher` `function` `load_daily`
- 命令 ≤300s：全链最长 231s（402 片重生成）/ 31.5s（单片判据）✓
- 派发前本地提交：`af0a0b06`（B121 复核入库）→ `99079a68`（G7）✓

**Round 8 判定：门禁通过**（判定发生在 G7 之后的完整重跑上，不是 B121 首跑）。

## V. 登记为下一轮开局的残项（不当作成绩）

1. **G7 缺变形牙**：本轮没有一条电池臂能在「G7 被 stub」时变红——`r8b121_*` 全部针对 G1–G6。
   Round 9 第一票必须补「else 臂唯一语句 = pure-none + 条件假边接入」的正反两臂。
2. `region_ast_generator.py:48342` 起 `_probe_keep/_probe_strip`、`region_analyzer.py:11451` 起 `_probe_*`
   是**已落地判据的局部变量命名**（无 print/IO，`check_patch_patterns.py` 判 PASS），
   按 rulers 口径不计调试残留，但命名误导，登记为清理项。
3. `handlers.get_*` 二轴（`elif …==3 and ==11` 臂 join + `else: return None`）、B117 (b) AND-leg 吞并与
   (c) 臂尾提升（`clock_worker`）、B122/B123/B124（仅语料、无合成孪生）、B99/B101/B114、
   genexpr 最小孪生、`r1_73` else-body-54 归属轴，以及 Task 8 的「已落地守卫外推/收缩复演」。
