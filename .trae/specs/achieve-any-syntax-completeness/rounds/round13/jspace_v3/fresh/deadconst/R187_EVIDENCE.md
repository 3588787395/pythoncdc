# rr-v5r187 — 推导式过滤位「折叠臂死常量」发射族（T2 常量对象 + T1 折叠真值 orelse 形态）

树：F:\Downloads\pythoncdc-main（未 commit / 未 push）；解释器 D:/Python/python.exe `-I -X utf8`
补丁：D:\temp\opencode\cl_layout\r187\fix187.py（anchor count==1 / utf-8-sig / py_compile / 幂等 / --revert 往返 sha 一致）
改动：core/cfg/comprehension_generator.py +92/−10（唯一文件；无 BOM + CRLF 逐字节保持）

## 1. 根因（实测定位，非阅读猜测）
- 探针 trace（`probe3.py`）证明两个站点都由 `_b256_filter_boolchain` 认领，且：
  - T2（e04 `<listcomp>`，池 `(0,)`）：emitter = `_parse_impl` 单块无条件跳转常量臂
    （旧 `:5809` `Constant(False if _cond == 0 else True)`），**不是** `_arm_const`/空段分支
    （trace 显示 5547/5761 未执行，5808-5811 执行）。
  - T1（r7_05 `<listcomp>`，池 `(2,True,0)`）：`_try_boolop` 产出 De Morgan 形态
    `not flag or x % 2`；既有 `_detect_comp_ternary_as_filter:6323` 折叠真值分支被 `_b256`
    抢先认领而不可达。
- 机制：CPython 3.11 把过滤位折叠臂常量登记进 `co_consts`（无 LOAD_CONST 引用=死常量），
  只发跳转发该值 ⇒ 同 `co_code` 对应多池。合成 `False/True` 会丢原件常量对象。

## 2. 修复（族级谓词，只读 CFG/常量表/极性）
1. `_b256_filter_boolchain(..., code_obj=None)`：调用方传本 code object（两处调用点）。
2. `_fold_arm_value(truth)`：池里已登记该真值的 bool ⇒ 发该 bool（对已 EQUAL 站点恒等）；
   池里没有该 bool 而有同真值死 int 项 ⇒ 发该项（0/1）；否则维持 True/False。
   接入 4 个折叠臂合成点：`_arm_const`、`_try_ifexp` 折叠臂、空段、单块无条件跳转臂。
3. `_try_folded_true_arm(_i,_end,_next_off,_cond)`：过滤位折叠真值 orelse 三元
   ——test 块末 FORWARD IF_FALSE 落通过点（`_blk_off(_end)`）、真臂块末 BACKWARD IF_FALSE
   落 `_next_off`；发 `IfExp(test, body=真臂, orelse=_fold_arm_value(True))`。
   **门控**：本 code object 池里存在**未被引用**的 bool `True`（原件发过真值常量臂的唯一
   指令侧痕迹；De Morgan 形态不 intern True），否则返回 None 维持原文本。

## 3. 目标站点（判官 semantic_diff.compare_case）
- 23/23 `DIFFERENT → EQUAL`（12 T2 + 11 T1），0 diff path。
- 产物变化（仅这两行）：
  - `[x for x in xs if (x if b else False)]` → `... (x if b else 0)`（池 `(False,)`→`(0,)`）
  - `if not flag or x % 2` → `if (x % 2 if flag else True)`（池 `(2,0)`→`(2,True,0)`，`LOAD_CONST 0` 索引 1→2 复原）
- 1180 条 callable J 条目逐条 A/B（oldtree 预处理树 vs 补丁树）：**仅这 23 条产物字节变化**，
  其余 1157 条逐字节相同（`old_decompile.py` 全量比对）。

## 4. 覆盖读数（coverage_checker.py，同一 space/judge）
(a) 任务口径（冻结 G3 证据 + 23 条新 semantic_runner 记录 overlay，g3fix 同款做法）：
`covered_5tuple 1151 → **1174**`、green 1151→1174、r7_only_different 29→**6**（=余下 T3）、
semantic_failures 29→6；产物 `work/semantic_r187_frozen_base_plus23.json`、
`work/coverage_r187_frozen_plus23.json`。

(b) 全量重跑（1180 条 callable 全部用当前树重解+重判；A/B 用 oldtree）：
| 读数 | 补丁前 | 补丁后 | Δ |
|---|---:|---:|---:|
| covered_5tuple | 1082 | **1105** | +23 |
| green | 1042 | **1065** | +23 |
| r7_only_different | 98 | 75 | −23 |
| semantic_failures | 138 | 115 | −23 |

**与任务给定 1151 基线的偏差（重要）**：1151 来自 round13 的
`gap/g3fix/semantic_v3m_b275_g3fix_merged.json`，该文件的产品集在当前树上不可复现。
实测：109 条当时 EQUAL 的条目在当前树（含 r186 HEAD、含 pre-r186 树）产物已漂移，
其中 69 条 R7-only、40 条含 R1 等行为维度（例 `JS-BOOLOP-008`：现树丢
`f_b98_while_cond_pos` 的 `if n > 2: break` 并把 `if i and (a and b or c or d)` 拆成嵌套 if）。
证据：基线产品文件仍在，当前判官判它 **EQUAL**；同一 pyc/source（sha 均未变）；当前 pre-patch
（HEAD）产物与基线产品文本不同。该漂移**不是本轮引入**（pre-r186 树同样复现），
故 1151 不是当前树的真实起点；本轮可交付的绝对读数即 1082→1105（增量恰为承诺的 +23）。

## 5. 五语料（treediff base=oldtree / fix=当前树，判官 scripts/pyc_verify.py）
| corpus | base sha | fix sha | 判官 base | 判官 fix |
|---|---|---|---|---|
| request | db2172e8f1a6 | db2172e8f1a6 | 194/194 | 194/194 |
| tarfile | 8b35ed1396ac | 8b35ed1396ac | 158/160 | 158/160 |
| cookiejar | d39c77eeb677 | d39c77eeb677 | 103/105 | 103/105 |
| subprocess | 557b9b0bfe9e | 557b9b0bfe9e | 75/78 | 75/78 |
| difflib | d70df6006a50 | d70df6006a50 | 62/62 | 62/62 |

difflib 任务给的 `07910868` 是 r184 期产物 sha（r185/r186 已变为 `d70df6006a50`）；
本轮 base==fix，且与 r186 基线（`r186/gate/base_products`）逐字节一致 ⇒ 五语料恒等。

## 6. 458 电池（D:\temp\opencode\cl_layout\r187\battery，old=oldtree、new=补丁树）
rows 458 / MISSING 0 / NO-SRC 0 / COMPILE-ERR 0；**TEXT-SAME 458，TEXT-DIFF 0**
（⊆ 17 允许集，集外 0；BYTE-EQUAL 空真）；`C7_skipedge` TEXT-SAME；
R110 169 案 text+sig 一致 **166/169（old==new）**（与 r186 读数一致；3 处为基线自身更差）。

## 7. AST / 红线
- 五语料 `(If, stmt, Pass)` base==fix：request(286,1725,17) / tarfile(324,1750,12) /
  cookiejar(240,1213,8) / subprocess(270,1125,22) / difflib(114,737,9)；逐 def/class 无差异。
  tarfile `next` source(11,43,0)=product(11,43,0)。
- 目标站点：e04 old==new=(14,70,0)、r7_05 old==new=(0,15,0)=源码；e04 源码(13,79,0)
  —— 该差为 fixture 既有形态归一（`if i: while i: return …` 被压成 `if i and i: return …`；
  该 while 体必 return、CPython 不发行回边，故字节等价、判官 EQUAL），base 产品同样如此，
  本轮 **old==new，未减少任何语句**。r7_05 与源码逐项一致。
- 红线（`gate/redline187.py`）：五语料 text=SAME、逐 code object changed=NONE；
  tarfile/cookiejar/subprocess 各 12 具名单元全 **BYTE-SAME**（38 案集合）。

## 8. 卫生 / 补丁自检
- `scripts/validate_region_generator_signatures.py` → `统计: 14 个错误, 6 个警告`（基线一致）。
- `core/cfg/comprehension_generator.py`：无 BOM（bom_count=0）、全 CRLF（crlf==lf=6691），
  与改前一致；`region_analyzer.py`/`region_ast_generator.py` 未改动，BOM `efbbbf` 单头。
- `git status`：仅 `core/cfg/comprehension_generator.py` M。
- fix187.py：二次 apply 全 skip；`--revert` → sha `515519bf6a5608f4`→`5efbf9508ae92ab1`
  （=改前原文 sha），再 apply → `515519bf6a5608f4`；两向均过 py_compile。

## 9. 产物清单（D:\temp\opencode\cl_layout\r187）
`fix187.py`、`probe1..4.py`、`judge_targets.py`、`r187_runner.py`、`old_decompile.py`、
`build_old_evidence.py`、`diag_pairs.py`、`battery187.py`、`battery_verify187.py`、
`gate/{corpus_run187,redline187,ast187}.py`、`work/{semantic_r187_shard0..7,semantic_r187_merged,
semantic_r187_old_merged,coverage_r187,coverage_r187_old}.json`、`gate/{raw_judge_*,corpus_run_*}`。
