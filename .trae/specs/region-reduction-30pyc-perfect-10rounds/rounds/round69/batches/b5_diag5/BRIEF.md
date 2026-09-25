# Round 69 · BRIEF · diag5（只读诊断代理）

你的工作区：`D:/Temp/opencode/r69gate` 的**同级**目录 `D:/Temp/opencode/r69gate/diag5`。仓库
`F:/Downloads/pythoncdc-main` 对你**只读**——不许写、不许跑任何 git 写命令、不许改 `*OK.py`、
不许动 `pyc_index.json`。你所有的镜像、产物、dump、日志、spec 都只放在自己的工作区里。

## 0. 硬性职务优先级（R65/R66/R67 的教训：代理死在 150 轮上限且什么都没留下）
**每完成一步就立刻把读数追加写进本目录 `FACTS.md`**（边跑边写，不要留到最后）。若被截断，
`FACTS.md` 必须已经包含 Step 0 和 Step 1 的实测表。
1. **Step 0（最先，约 3 分钟）**：在 `--arm=landed`（＝当前工作树字节）上复放你自己靶支的读数，
   必须与 `targets.md` / 本 brief 的预读数**逐字段相同**；不同就以你的实测为准并写「对 BRIEF 的更正」。
   ```
   python -X utf8 h62.py run --arm=landed --list=targets.txt --out=dump/landed.jsonl
   python -X utf8 h62.py run --arm=landed --list=canary.txt --out=dump/landed_canary.jsonl
   python -X utf8 closeout67.py battery landed          # 45 项公开电池（自动发现 test_repros/round63..67）
   ```
2. **Step 1**：对每个 code object 的归一化 hunk 表 + 归属（用 `nested_diff.py`，它按 code-object
   全路径配对；`nhunks.py` 有已知缺陷，见 §5）。要区分「真缺陷」与「NOP/EXTENDED_ARG 计数伪影」。
3. **Step 2**：对你名下的每一个缺陷函数给**根因判定**（哪个函数、哪一层、哪个早退把语句或结构
   丢掉了），必须在生成器/分析器里**实测**（打印或写探针），不许只凭读代码推断。
4. **Step 3**：为你攻的那个形状做**最小合成复现**（`synth/`，编译出 .pyc，配 `synth/*.txt` 名单）。
   没有合成复现**不许**写 spec（这是硬规则）。
5. **Step 4**：候选判定：`specs/cand_r69_<名>.json`（`mk_spec.py` 或手写），自己做 A/B：
   `python -X utf8 h62.py build --spec=specs/xxx.json --dst=<你的臂名>`，然后同臂跑 targets /
   battery / canary / 合成，并用 `h62.py ab` 出 TALLY。严格尺：`python -X utf8 sstrict67.py
   <臂名> <名单>`（能配对 scratch 路径）。
6. **Step 5**：收口 `FACTS.md`：Step 0-4 全表 + 逐靶 **VERDICTS** + 「候选：NONE/名字」+
   「对 BRIEF 的更正」。

## 1. 可落地文件（**三个**，h62/mbuild69/land69 的白名单已含全部三支）
- `core/cfg/region_ast_generator.py`（区域→AST 发射）
- `core/cfg/region_analyzer.py`（CFG→区域归约）
- `core/cfg/comprehension_generator.py`（推导式/聚合内三元重建）

**禁止**提出需要改其它文件（`scripts/`、`_r10_strict_check.py`、其它 core 模块）才能生效的候选：
那类只写进 `FACTS` 的「中心级建议」，不要做成 spec。

## 2. 判据纪律（用户的长期 mandate，违反即被中心回退）
- 只许**同层次结构身份**：读**本区域/本块自身**的字段（`entry`、`blocks`、`merge_block`、`exit`、
  `parent`、`then_blocks`、`else_blocks`、`condition_block`、`chained_compare_ops/blocks`、
  块内指令与本块栈效应）。
- **禁止** `region.entry in r.blocks` 型跨区域跨层次包含；禁止按函数名/文件名/字节码偏移/
  计数阈值/魔法常量的启发；禁止新增 `self` 状态；禁止破坏「innermost→outermost、每块每层唯一
  归属」。
- 每条新规则必须把**三要素写进识别方法注释**：识别条件（结构判据）、归约方式（区域如何折叠）、
  AST 映射（发射成什么节点）。缺任一要素视为未完成。
- 单向数据流、一次正确：不许写「先发射后正则修文本」这类补丁。

## 3. 采纳合同（全满足才算候选；中心会独立复测，任何一项不过即回退）
1. 金丝雀 4 支产物 sha **逐字节不变**：`4d41187e356544e0`（quotation 143/143）、
   `af77224b34b203c4`（market_time 10/10）、`e711b8ea86d49a15`（IQCommon datetime_func 26/26）、
   `9d09af09249da177`（IQData datetime_func 25/25）。
2. 45 项电池**不得劣于 landed**（`worse-than-landed=0`）。
3. 名下靶支严格变好，并满足 **ADR-1 判据**（R68 更正后的两支，`rounds/round68/specs/ADR-1`）：
   - **缺失/过冲族**（`seq_len`，decomp 条数 ≠ orig）：该缺陷族 Σ|orig−decomp| **净减少**，
     且不得以少发射换（丢语句不算修好）；
   - **纯位移族**（counts 相等、严格尺 `seq_diff`/`target_diff`）：**归一化 hunk 数严格下降 +
     first_diff 回移 + Σ|Δ| 不升 + 严格尺不得新增 `target_diff`**，且必须成对落地。
   形状移动但 Σ|Δ| 不变（位移族无 hunk 收益）即拒，R67 diag3 即因此被回退。
4. 无 ERR、无不可反编译；锚点在当前落地字节上 `count==1`。
5. 你自己的合成见证必须咬合（landed 失败、你的臂通过）。
6. **不得跑 402 全量扫描**（那是中心的活，跑它会吃掉你的轮次预算）。

## 4. 轮初基线（中心 landed 实测，作你的 A/B 对照列）
- 10 支 partial 官方尺：**412/449 matched**、缺陷函数 **37**、Σ|Δ| **256**、Σjumpdiff **151**、ERR=0。
- 45 项电池 landed：**182/200**、缺陷函数 **18**、worse=0、ERR=0。
- 严格尺（R68 收口，跑在已发布产物上，仅这 10 支）：**433/488**、缺陷函数 **55**、missing=0 extra=0。
- 轮初发布口径（官方尺 `stats`）：**5746 funcs / 5709 matched / 99.36%**，ok 392、partial 10、failed 0。

## 5. 仪器已知缺陷（绕法，别再花时间重发现）
- `nhunks.py`：未对 `EXTENDED_ARG` 归一（跳距跨 255 会多出指令被当成真缺陷）；按 `co_name`
  唯一匹配同名 code object（如 `scheduler.pyc` 的 `run_daily`@72/@255）会**直接 AssertionError**
  ⇒ 用本目录 `nested_diff.py`（按 code-object 全路径 `<parent>/<name>#<const-idx>` 配对）。
- `cstrict.py` 的产物名推导只认 `site-packages/` ⇒ scratch 合成件用 `sstrict67.py` 或官方尺。
- `regdump.py` 不打印 `handler_entry_blocks`/`except_handlers`。
- `h62.py run --out=<已存在文件>` 会按 `arm|path` **跳过全部记录**（resume 语义）⇒ 换臂名就换
  out 文件名。
- 臂名空间共享：中心也用 `c1` 之类的短名，你的臂名请带 `r69diag5` 前缀避免互相覆盖。
- `core/cfg/region_analyzer.py` **没有模块级 `import dis`**（只有 `import dis as _dis` 与三处
  函数内导入）⇒ 在 analyzer 里用 `dis.stack_effect` 必须**局部 `import dis``，否则 NameError
  被上层宽 except 吞掉、产物静默退化成垃圾而不报错（R67-diag5 实测 `[36,28,0,29]`）。

## 6. 落地字节上的当前站点（本轮 grep 实测，行号即最终字节）
generator：`_loop_build_if_with_exit_branches` L10039（定义）/L10603（调用点）、
`_fold_header_then_continuation` L10499（R68 新 helper，三要素在 docstring）、`_r68_branch`
L10621 起（R68 新）、`_handler_backedge_is_explicit_continue` L20265、
`_build_ternary_boolop_condition` L34414、`_r67_split_cc_ternary_stmt_prefix` L35262、
`_try_build_ternary_kwarg_call` L42495（定义，调用点 L42508）、`_split_block_condition_prefix`
L324/L336（栈深归零划界）；analyzer：`_should_skip_block_for_if_region` L15436、
`_can_be_ternary_header` L20300、`_detect_ternary_pattern`（多处）、`_mb_first_store_idx`
L21981-21988（内联）、`_chain_merge_candidates` L18640 起；comprehension：
`_detect_comp_ternary` L1601、`_r67_boolop_chain_end` L1641、`_detect_comp_ternary_as_filter` L1846。
R68 刚落地的标记（改同族判据前先读它们，别撞车）：analyzer `[R68-diag5]` L408/L19745、
`[R68-b2 and-chain]` L16841、`[R68-B]` L26938、`[R68-E]` L26944/L26990、`[R68-C]` L27069；
generator `[R68-b2 cell-swap]` L14480/L47903、`[R68-D4-ORCHAIN-TAIL]` L17843。
**行号会漂移**：动手前先 `grep -n` 复核你自己那条锚点。

## 7. 报告格式（`FACTS.md`）

```
## Step 0 · baseline replay   （逐字段贴你的 landed 读数 + 是否与 brief 相符）
## Step 1 · hunk tables       （每支每 code object 一行：orig/decomp、归一化 hunk、真缺陷 or 伪影）
## Step 2 · 根因              （文件+行号+早退条件+实测打印）
## Step 3 · 合成复现          （synth 文件名、landed 读数、失败签名）
## Step 4 · 候选与 A/B        （spec 路径、判据三要素、targets/battery/canary/strict/synth 五列读数）
## VERDICTS                   （逐靶支：候选：NONE / 候选名 + 理由）
## 对 BRIEF 的更正            （任何前提不成立都写在这里，中心会读）
```

## 8. 你名下 2 支：`trade_info_utils` 39/40、`risk_calculation/__init__` 33/35
- `trade_info_utils` 官方只剩 `trade_operation 304/302(hunks=2)`（R68 轮初还有 `get_trade_list
  339/323`，已修掉）；严格 37/41（R68 起点 37/41，未动），余 4 缺陷：`get_trade_status #70
  FOR_ITER 终点`、`get_trade_unit_info seq_len 240/241`、`set_trade_status #113 JUMP 终点`、
  `trade_operation seq_len 304/302`——**没有一个在官方尺里**（官方 counts 已近平）。
  R64 教训：diag3 曾有判据在 `trade_operation` 上**过度剪枝**，任何剪枝型判据都要过 45 项电池。
- `risk_calculation::__init__`：`_on_publish_after_trading_end 486/481`、`_save_testds_to_csv 71/68`
  （严格 488/481、75/68）。R67-diag6 实测同族三签名：
  (a) try/loop-exit 的 `JUMP_FORWARD` 被改写成 `LOAD_CONST None`/`RETURN_VALUE` 互换
  （**R47 禁令约束 Expr→Return**）；
  (b) `IMPORT_FROM THREAD_STATUS`（原为名字加载 + `POP_TOP` 丢弃）被物化成 `STORE_NAME` + `if`；
  (c) 外层 `while` 失去回边（`JUMP_BACKWARD`→`JUMP_FORWARD`）导致**重复发射**第二个循环。
  `_on_set_positions` 只有严格 `[seq_len] 297/298`（官方已 OK，属 (c) 的回边重放置）。
  (a) 受 R47 禁令约束；(b)/(c) 未被禁，且 (c) 与 diag4 名下 realtime `clock_worker` 的重发
  问题同源——若能协同给出更好。
- 你名下只有 2 支、累计官方 gap 3，优先把时间花在**根因实测 + 合成复现**上，凑数候选会被 ADR-1
  直接回退（诚实 NONE 优于过重的规则）。