# Round8 · FIX_IMPLICIT_RETURN_ARMS —— 隐式 return None 的「逐边落点」成员关系判据（R8-B121 sinkarms）

分支 `rr-v3r01-f557fd` / 工作树 `D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main`
判据 `scripts/pyc_verify.py`（未改动）；尺子 `compare_pyc` sha256(16)=`9c7567bd6776b36b`，解释器 3.11.7。
scratch `D:/Temp/rrv8/`（探针 `probe_ft.py` / `diag_b121.py` / `var_gen.py` / `gen_b121*.py`、备份 `bak/`）。
产物一律「删除 + `python -X utf8 pycdc.py -o <base>OK.py <pyc>`」重生成；**未手改任何 \*OK.py**。

## 结论

**「代码已落地」**。主目标 `site-packages/fly/common/flytools.pyc` 由 **65/66 → 66/66 status=success**（重生成产物实测）。
兄弟目标 `function.pyc` 70/71、`handlers.pyc` 29/30 **未翻**（不同轴，见 §6）。无 pin 下降，无电池回归。

---

## 1. 规则（一句话）

> 在一个 code object 图内，当且仅当 **不存在任何「汇合 return 块」**（`_is_return_none_join_block`，
> 即 [r1-b98-exitjoin]/[R5-B72-B]/[R57-C] 已登记的「源码显式 `return None` ⇒ ≥2 前驱或无条件跳转接入的汇合块」
> 身份证据）且存在 **≥2 个互不相同、单前驱、以隐式 return None 收尾** 的终块，并且每个这样的终块都
> ①形态属 'pure-none' / 'handler-epilogue'（块内无用户语句）、②由前驱的**控制转移边**接入（条件跳转的
> argval 目标，或剔除异常边后的顺序 fall-through）、③**不是条件测试块的顺序落点**（G4b：那是对应 then
> 臂的入口）、④前驱与本块**同属至少一个区域**（`self.regions` 成员集合）、⑤本块不在
> `_with_jump_exit_blocks()`（F5）——这 **一组终块全体**判为「函数隐式尾声的逐边落点」，不是语句：
> 生成端不发射（登记 generated / generated_offsets、返回空语句列表），重编译时由所属语句自然再生每边一份落点。

落点站点：`core/cfg/region_ast_generator.py` 新增
`_r8_b121_scope_return_sink_kind`（块形态类别）、`_r8_b121_implicit_tail_landing_sinks`（G1–G6 + 全有或全无门，按实例缓存），
消费点唯一：`_generate_block_statements` 单一漏斗（紧接 [R5-B119 loopsink] 之后一处）。
**全有或全无**：任一候选块不满足即整集为空——绝不半抑制（否则臂尾与体尾被拆开，落点次序反被重排）。

## 2. 五条线各自靠什么成员证据被抑制（`modify_batcktes_info`，运行时实测 `D:/Temp/rrv8/diag_b121.py`）

产物行 → CFG 落点块 → 证据：

| 产物行（修复前） | 落点块 | kind | 唯一前驱及其块末 opcode | 同区认领（原则2 面） | 判定 |
|---|---|---|---|---|---|
| 805 `return None`（`with FileLock(...)` 体末） | off722 | pure-none | 700 = `POP_TOP`（__exit__ 清理块），顺序落点 | TryExceptRegion@4 ∩ WithRegion@4 | 边的落点，非语句 |
| —（异常传播支路，原本未发射） | off748 | pure-none | 742 = `POP_TOP` | TryExceptRegion@4 | 同上（登记后为 no-op） |
| 812 `return None`（`elif …: log.trade_norm.info(ex)` 臂尾） | off906 | handler-epilogue | 854 = `POP_TOP`（臂体收尾）顺序落点 | TryExceptRegion@4 ∩ IfRegion@776 | 臂正常路径到达区域共享尾 |
| 814 `return None`（`else:` 空臂） | off930 | handler-epilogue | 842 = `POP_JUMP_FORWARD_IF_FALSE→930`（跳转目标，非顺序落点） | TryExceptRegion@4 ∩ IfRegion@776/772 | 同上 |
| 815 `return None`（`if log:` 链尾） | off942 | handler-epilogue | 788 = `JUMP_FORWARD→942` | TryExceptRegion@4 ∩ IfRegion@772 | 同上 |
| 817 `return None`（外层 `else:` 空臂） | off918 | handler-epilogue | 772 = `POP_JUMP_FORWARD_IF_FALSE→918` | TryExceptRegion@4 ∩ IfRegion@772 | 同上 |

抑制后，两条空 `else:` 子句随语句消失而整体不再发射（不塌成 `pass`、无死代码）：产物 812–817 六行、805 一行全部归零。
**805 与 812–817 是同一判据的两个形态类**（'pure-none' 体尾 / 'handler-epilogue' 臂尾），不是两条规则。

## 3. 重生成产物 diff（flytoolsOK.py）

37794 B → **37571 B**；本单元 790–817 → 790–811；删除行（逐字）：
```
805                return None
812                    return None
813                else:
814                    return None
815                return None
816            else:
817                return None
```
其余各行逐字节不变。判据：`status=success units=66/66`（原 `***<module>.ProcessWrite.modify_batcktes_info: Failure: Different control flow` 消失）。
这与 REVIEW_NOP §1.3 探针 P5b 的测量形状一致（本轮把它下到了发射端）。

## 4. 判据的可区分性：CPython 3.11 控制实验（`D:/Temp/rrv8/var_gen.py`，本机同解释器）

| 源形 | 终块（隐式 None 返回） | 汇合块？ |
|---|---|---|
| v_a 臂不写 return | off34 preds=[4] + 4 个退栈对落点，各 1 前驱 | **无** |
| v_b 臂写 `return None`、无尾语句 | off34 preds=[4] + 4 个退栈对落点，各 1 前驱 | **无**（与 v_a 逐块同形 ⇒ 源码层不可辨识，同 R4-B116/R5-B119 自陈） |
| v_c 臂写 return **且**函数尾写 return | 尾部纯 sink preds=[34,196] | **有** ⇒ 不抑制 |
| v_d 臂不写、只尾写 return | sink preds=[34,174] | **有** ⇒ 不抑制 |

⇒ G1（无汇合块）正是把 r8nop_07（v_c 形，MATCH）与 r8nop_06（v_a 形，MISMATCH）分开的那条轴；v_a/v_b 同形是本族固有歧义，按已落地的 B116/B119 立场取「不发射」。
G4b 的必要性同样实测：`flytools::write_backtest_info` 的 off248（pred 182 `POP_JUMP…IF_FALSE→252` 的顺序落点 = `if datadict == self.default: return None` 的 then 臂）与 off498（pred 484 →510 同形）都是**真语句**；关掉 G4b 后本判据在该单元命中，flytools 立即退回 `65/66`（失分单元换成 `write_backtest_info`，实测 JSON 于 `D:/Temp/rrv8/deform/`）。

## 5. 电池读数（守卫在位，产物全部重生成）

| 电池 | 期望 | 实测 | 判定 |
|---|---|---|---|
| `r8_probe_index`（25→29 arms，25 条原路径全部保留 + 各自 sibling `*OK.py`） | baseline 41/50（25 文件 16/9） | **52/58 units，23 success / 6 failure** | +3 翻正（06 15 20），新 4 臂全绿，无回归 |
| `r6_probe_index` | STAY 76/85，31/9 | **76/85，31 success / 9 failure** | STAY |
| `r1_probe_index` | STAY 108/110，44/2 | **108/110，44/2** | STAY |
| `r1_regress_index` | STAY 34/34 | **34/34** | STAY |
| `r2v3_probe_index` | STAY 105/126，41/21 | **105/126，41/21** | STAY |
| `r4_probe_index` | STAY 77/87，30/10 | **79/87，32 success / 8 failure** | **+2 翻正，0 回归** |
| pytest 六文件 | 277/2/2，同两条 | **2 failed, 277 passed, 2 xpassed**（`test_B01_simple_if_then_else_merge` / `test_BOUNDARY_02_large_function`） | STAY |
| import + `compileall -q core` | OK | **IMPORT_OK / COMPILEALL_OK** | STAY |

单文件：flytools **66/66 success**；function 70/71 failure；handlers 29/30 failure。

## 6. pins（34 项，`D:/Temp/pins_r8.json`，产物逐个重生成）

quotation **153/153**、quote_handler **79/79**、profiler_func(IQEngine/utils) **18/18**、cgroup_utils 8/8、email_utils 4/4、
calexrights_func(IQData/utils 与 plugin_system_fly_basicdata) **8/8 ×2**、trading_dates_mixin 14/14、stock_position 37/37、
future_contract_info 29/29、fly/logger 64/64、ptradeAccount 137/137、executor 10/10、history_api 19/19、
strategy(plugin_fly_data) 26/27、api_base(IQData/api) 27/28、matcher 16/17、finance(IQCommon/data) 31/32、
bar(IQEngine/core) 84/85、load_daily 26/27、strategy_universe 10/11、realtime_event_source 12/13、
**quote 86/92 → 87/92（+1 翻正）**、klinedata 61/64、wizard_quant_api 55/58、real_quote 43/45、
risk_calculation/__init__ 41/43、order_api 35/37、trade_info_utils 37/41、trade_live_broker 118/128、
handlers 29/30、function 70/71、**flytools 65/66 → 66/66**。
合计 1462/1503 units（含一个我在索引里误纳的诱饵 `email_utils.py.pyc`，判为 `error` 0/0，非语料 pin、与修复无关）。
**没有任何 pin 的 unit 数下降** ⇒ 无 over-claim 迹象。

未翻的兄弟目标（如实声明）：
- `function.pyc <module>.reconnect` 70/71 —— N3 轴（`while <cond>:` 被判为 `while True:` + 体内守卫，站点 2 `region_analyzer.py:515/685/1366/4563` 的条件块归属），本判据不触及；实测 SET 未在该单元命中。
- `handlers.pyc <module>.TWHThreadController._target` 29/30 —— FIX_TAIL_RETURN_LIFT §6 已定为「and-chain arm join + 尾部复制叶子吸收」第二轴；本票只裁隐式尾声落点，不裁臂汇合，故不覆盖（未强行推动）。

## 7. True-hits vs flips

- **True-hits（判据命中）**：flytools `modify_batcktes_info` SET=[722,748,906,918,930,942]（6 块，抑制 5 条可见语句 + 1 条本未发射）；
  r8nop_06 / r8nop_15 / r8nop_20 / 新臂 r8b121_01 / r8b121_02 所在单元命中；r4_probe 2 单元命中。
- **可观察 flips（判据单位数变化）**：flytools +1（65→66）、quote +1（86→87）、r8_probe +3 units（06 15 20 由 MISMATCH→MATCH）、r4_probe +2 units。
  合计 7 个单元翻正，**0 个单元翻负**。
- 判据被正确拒绝的站点（保守性 True-reject，非 flip）：r8nop_07/14/19/25、r8b121_03/04、`write_backtest_info`（G1/G4b 各自生效）。

## 8. 变形 arm（第 4 项交付，已追加 4 条到 `test_repros/round8/r8_probe_index.json`，25→29）

| arm | 形状 | 守卫在位 | 变形（唯一改动） | 变形读数 |
|---|---|---|---|---|
| `r8b121_01_except_arms_empty_else` | `except … as e:` 内 `if/elif` 双臂 + 空出口，无汇合块 | success 2/2 | stub `_r8_b121_implicit_tail_landing_sinks` → `set()` | **failure 1/2**（臂尾 `return None` 复活） |
| `r8b121_02_with_body_and_arms` | `try: with CM(x): do(work)` + 双臂（with 体尾 + 臂尾两类） | success 2/2 | 同上 stub | **failure 1/2** |
| `r8b121_04_explicit_arms_plus_tail` | 臂写显式 `return None` + 函数尾再写一条（汇合块存在） | success 2/2 | patch `_is_return_none_join_block` → `False`（撤 G1） | **failure 1/2**（真语句被吞） |
| `r8b121_03_two_handlers` | 两个 handler、臂不写 return（常驻负对照） | success 2/2 | 三种变形均绿 | 负对照：钉住「不因多 handler 而扩大」 |
| G4b 轴 | — | flytools 66/66 | 源码内把 G4b 条件置 `False and …`（临时变形，测后按字节还原，sha256(16) 前后均 `4a9bf374caa7fa63`） | **flytools 65/66**（失分单元 = `write_backtest_info`） |

变形读数写在 `D:/Temp/rrv8/deform/`（stub 产物与判据输出），索引读数 `D:/Temp/b121_mini.json`、`D:/Temp/r8_r8.json`。

## 9. 死判定删除与字节事实

- 已删除 REVIEW_NOP §4 站点 1 的死块（置 0 / +1 的 trailing-return-None 出口计数 + 守卫体为 `pass` 的消费 if）。**本票规则即其替代品**：
  同一问题改由成员关系裁决并接入发射端。删除后 `grep -c "_trailing_rn_exit_count" core/` = **0**；
  `region_analyzer._check_block_has_trailing_return_none` 保留（仍被本票与 B116/B119 使用）。
- residue greps：`R8-B120`（上一票回退标记）=0、`False and _pli`=0、`_fallback_/_workaround_/_hack_/_temp_` 在本票新增代码中 0（仓内既有计数不变）。
- 字节事实（intake → 落地）：
  - `core/cfg/region_ast_generator.py` 3691860 B / 58769 CRLF / 1 leading BOM / sha16 `2e3051ed3614bd91` → **3705035 B / 58966 CRLF / BOM 保持 / LF-only 行 0 / sha16 `5f22a856371b5f59`**。
  - `core/cfg/region_analyzer.py` **未改动**：2058547 B / 32336 CRLF / BOM / sha16 `38a1d5142d132fd7`（= intake）。
  - `core/cfg/code_generator.py` **未改动**：299897 B / 6022 CRLF / 无 BOM / sha16 `28aba10bae133952`（= intake）。
- marker 前缀计数（`core/cfg/*.py`，文本出现次数）：既有 `[R2-B106`=4、`[R2-B107`=7、`[R2-B108`=5、`[R3-B115`=1、`[R3-B109`=3、
  `[R6-B111 armscope`=3、`[R7-B117 exitclaim`=3、`[R5-B100-armjoin-trueentry`=4 **逐项不变**；
  `[R4-B116 sinkexit` 4→5、`[R5-B119 loopsink` 3→6 的增量**全部来自本票 docstring/注释对这两条既有判据的交叉引用**（原 4 个 B116 站点
  `region_analyzer.py:28031/28245/28253/28630` 与 3 个 B119 站点 `region_ast_generator.py:51519/51563`、`region_analyzer.py:28135` 逐处未动）；
  新标记 `[R8-B121 sinkarms` = 4（两个新方法各 1、漏斗消费点 1、函数体注释 1）。

## 10. 本轮改动清单

- 生产代码：`core/cfg/region_ast_generator.py` 单文件（2 个新方法 + 1 处漏斗消费 + 1 处 docstring ③ 更新 + 1 处死判定删除 + 1 处注释）。
- 标本：`test_repros/round8/r8b121_01..04`（`.py`/`.pyc`/`OK.py` 各 4）+ `r8_probe_index.json` 25→29 条（原 25 条路径与 sibling `*OK.py` 全部保留，实测 `missing pyc [] missing OK []`）+ 辅助 `r8b121_mini_index.json`。
- 语料侧：按认证方式重生成 flytools / function / handlers / 34 项 pin 产物；**未手改任何 \*OK.py**；未动 `scripts/pyc_verify.py`、`pycdc.py`、`rules.md`。
- 未跑 402 文件批与 34 集（并行会话占机）；未闭合残差见 §6。
