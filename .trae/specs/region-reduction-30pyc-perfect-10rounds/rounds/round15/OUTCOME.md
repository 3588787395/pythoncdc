# Round 15 结果（OUTCOME）

本轮两条根因线，按门禁顺序完成：单点修到完全 OK → quotation.pyc 单验 → 全量批量回归 → 归因 → 提交 push。

- **15-A（A2 族）**：前置语句「发射权」的指令粒度登记（`prefix_emitted_upto`），
  解 `BoolOpRegion ↔ IfRegion` 双向认领下的重复发射／整段丢失。
- **15-B（H1 + H2）**：else 臂对「双角色块」的收养 + owner 的识别与发射权解耦。

详细判据与注释落点见 `fixes.md`（同一文件的两节）与 `elsearm-design.md`（设计稿 → dry-run → 定稿）。

## 一、口径（两把尺子，数字不得互相减法）

| 口径 | Round 14 记录 | Round 15 实测 |
| --- | --- | --- |
| 官方 loose（`pyc_index.json` 402 文件，`scripts.pyc_batch_verify.bytecode_diff`） | 353 ok / 49 partial，函数 5617/5746 = 97.75% | **355 ok / 47 partial，函数 5619/5746 = 97.79%** |
| 严格尺子（`_r10_strict_check` / `D:/Temp/r13_all_ok_check.py`，405 targets） | 329/405 文件 = 81.23%，函数 6093/6332 = 96.23% | **331/405 文件 = 81.73%，函数 6095/6332 = 96.26%** |

两把尺子的增量都是 **+2 文件 / +2 函数**，与本轮翻正清单（下表）逐一对应。
日志：`D:/Temp/r15_official.txt`、`D:/Temp/r15_strict_all.txt`。

## 二、本轮翻正清单

`IQData/utils/arg_checker.pyc` 与 `IQEngine/utils/arg_checker.pyc` 是同一份源码的两个包内副本
（重复源策略），一处修复同时翻正：

| pyc | 修复前（HEAD 产物） | 修复后 |
| --- | --- | --- |
| `IQData/utils/arg_checker.pyc` | official 38/39、strict 38/39 | **official 39/39 rate=1.0、strict 39/39** |
| `IQEngine/utils/arg_checker.pyc` | official 42/43、strict 42/43 | **official 43/43 rate=1.0、strict 43/43** |
| `IQCommon/arg_checker.pyc` | official 46/47、strict 48/49 | 46/47、48/49（计数不变，见 §四的代价） |

⇒ 「每一轮至少解决一个 pyc」达成：**2 个 pyc 由 partial → 100%**（两把尺子同时）。

## 三、验收工序与复现电池（全部为落地后终态复跑）

```
test_repros/round15_arm    repros=12 MISMATCH=4 MATCH=8  UNEXPECTED=0 NOT-REPRODUCED=1  （本轮新建，9→4）
test_repros/round14_join   repros=16 MISMATCH=1 MATCH=15 UNEXPECTED=0                   （10 项已改标 SENTINEL，无 REGRESSED）
test_repros/round14        repros=17 MISMATCH=0 MATCH=17 UNEXPECTED=0
test_repros/round13        repros=25 MISMATCH=14 MATCH=11 UNEXPECTED=0
quotation.pyc 单验          147/150，缺陷集合逐函数与基线相同 ⇒ 与本轮无关（产物门记 WORSENED(回滚)，属 SubTask 13.3 漂移）
全量产物门 406 targets      CLEAN=329 UNCHANGED=65 WORSENED(回滚)=9 REGRESSION(回滚)=2 NO-OKPY=1
31 文件内存严格 A/B          445 identical → 447，其余 28 项逐文件不变
```

9 WORSENED + 2 REGRESSION 的文件集合与 Round 14 的 `D:/Temp/r14_gate_c1.json` 逐个相同，
其中 5 项再用 pre-patch 副本内存复算与门内 after 值完全对齐 ⇒ **本轮零新增回退**
（归因细节见 `fixes.md` §Round 15-B / §3）。

## 四、已登记的代价与产物变更

- **`IQCommon/arg_checker._is_valid_quarter` 缺陷变大**：同一条严格判据下缺口从 2 条指令
  增至 16 条（`orig=90 decomp=74`）。函数级计数不变（48/49），因此两把尺子都没反映成回退，
  但复现 `r15a_01`／`r15a_02` 仍是 MISMATCH。
  ~~根因是 H1+H2 复原了外层 `if` 之后，其 then 臂里的 `TryExceptRegion@84` 在分析层不是
  `IfRegion@76` 的子区域~~ ⇒ **该猜想在 Round 16 被实测否证**：区域树里
  `TryExceptRegion@94.parent` 正是 `IfRegion@86`（结构层没问题），真正的原因是
  `_if_generate_then_branch` 的「表达式子区域预生成」把 `BoolOpRegion@94` 的 blocks 全量
  写进 `generated_blocks`，而这批块恰等于 `TryExceptRegion@94.try_blocks`，随后
  `_try_entry_generate` 见入口已 generated 即空转。证据与复现见
  `test_repros/round16_arm/` 与 `rounds/round16/arm-design.md`。
  **属生成层发射权缺陷，列入 Round 16 第 1 项**，不用别的补偿掩盖。
- **`pyc_index.json`**：`IQCommon/arg_checker.pyc` 条目原记 `decompile_status=ok /
  bytecode_match_rate=1.0 / matched_functions=47`，实测为 46/47（且 HEAD 产物同样是 46/47，
  说明这是 Round 10 的未验证 stale 标记，不是本轮造成）。按既有 `index-corrected` 惯例
  逐字段纠正（+2 行，`git diff --numstat` = 5/3）。两个翻正条目本来就已经是
  `39/39`、`43/43` rate=1.0，无需改动。
- **`site-packages/IQCommon/api/klinedataOKOK.py`、`klinedataOK_checkOK.py`**：
  全量产物门按当前 core 重新生成的副产品（HEAD 与工作树严格计数完全相同：53/63、54/63）。
  一并提交以保持产物与当前 core 一致。

## 五、Round 16 交接清单（按优先级）

1. **analyzer 层：then 臂内 Try 的父链归属**（`IfRegion@76` ⊃ `TryExceptRegion@84`）——
   修 §四的 `_is_valid_quarter`（16 条指令）并顺带解 `r15a_01/02`、`r14j_09_try_in_else_arm`。
2. **R13c「sink 塌陷」**：`region_analyzer` ≈L17090
   `if not _25b_else_is_cond and self._if_arm_is_sink(...) and _R15_SINK_OK(else_succ):`
   关闭该塌陷的 A/B 已完成（`D:/Temp/r15_elsearm_diag/d11_probeA.py`、`cmp3.txt`：
   基线 257 函数缺陷/79 文件 → 250/77，FIXED=7 BROKEN=0 CHANGED=1）。
   目标：`IQData/manager/plugin_manager.pyc`（9/10）与 `IQEngine/core/plugin_manager.pyc`（8/9）
   的 `set_engine` 同时翻正。
3. **`_value_merge_hosts_next_if` 过宽／R36 否决过窄**：`r15a_08` 的
   `guard_clause_prefix_end` 目前只为裸名条件写入，链式比较作条件时被 R36 整块跳过
   （`orig=41 decomp=19`）。
4. **body-sequence 重复发射族**：`r15a_09`（`orig=39 decomp=48`，多 9 条）。
5. SubTask 13.3 的 11 项 Round 13 遗留债、SubTask 13.4/A-2、Round 14 backlog
   （`IQCommon/util/replace_utils` 差 2 个函数、`cgroup_utils`、`decrypt_database_url` +29、
   `IQEngine/utils/profiler_func` 16/17）。

## 六、核心改动与文件指纹

- `core/cfg/region_ast_generator.py`（UTF-8 BOM + 纯 CRLF）：
  `dc4bf5857f3a42a5 → d5a827199240447b → 4081092974cdecb4 → 9407806fb72c2103 →
  30ed9522ca00c94d → 7c5ffe968232806d → f8debe9af6b60b20`（15-A 终态）
  `→ d07996aaa20d4665`（15-B 落地，行数 48070 → 48122，字节 2957878 → 2962083）。
- `core/cfg/region_analyzer.py`：**本轮零改动**，sha 仍 `110bf739bde62846`。
- 补丁/验证脚本全部在 `D:/Temp`（`r15_h1_patch.py` 6 hunk 断言式字节补丁、
  `r15_make_base_copy.py` 反向重建、`r15_h1_dryrun.py`/`r15_seed_any.py` 副本播种），
  仓库内不落盘。
