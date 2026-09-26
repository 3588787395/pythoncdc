# R71 · fix2（修复工程师，P1 族 F-THENOVER）BRIEF

## 0. 使命

你是 Round 71 的第二位修复工程师。repo（`F:/Downloads/pythoncdc-main`）**只读**，
你的工作区：`D:/Temp/opencode/r71gate/fix2`（仪器已就位，`DIAG1_FACTS.md` 是测试工程师的
根因事实书）。基线 HEAD = R70 落地 `b21c5c61`；h62 `--arm=landed` = repo 字节。

**唯一目标族：F-THENOVER / F-ABSORB（diag1 FACTS §3.1，68+17 单元的最大主族）**
—— 分支/循环帧内的生成器错误认领**兄弟区域**，导致跳转落点从近端 merge 变成远端 end、
后续共享语句被吸进当前分支。已定位到行：

- `core/cfg/region_ast_generator.py` `_process_if_blocks`（def `:21468`），
  **guard 在 `:22445-22450`**（现 5 条，第 (5) 条 `merge_block is None and exit is None`
  是历史为保 `quotation::get_trend` 金丝雀逐字节而**故意收窄**的，注释见 `:22420-22421`）；
  认领动作在 `:22451-22465`；
- 调用链实证：`_generate_region(:3157)→_generate_loop(:4120)→_loop_generate_for(:4427)→
  _if_generate_branch_stmts(:4426/:4897)→_process_if_blocks(:21430/:22454)`；
- 同型既有判据（可借鉴的结构身份写法）：`ra-gen:21694-21704`（`_fis_is_ancestor_merge`）、
  `ra-gen:21745-21753`（隐式 `return None`）；
- analyzer 侧无过错（t01 探针：3 个 `parent=None` 顶层区域树正确，是 generator 发射层级错）。

## 1. 步骤

1. 读 `DIAG1_FACTS.md` §3.1/§3.7 与 §5 提案；读 synth 复现清单（`D:/Temp/opencode/r71gate/diag1/synth/`，
   重点 t01、t02、t22——已实测 status=failure）。
2. 在你工作区复现：把 synth `.py` 编译成 pyc，`python -X utf8 F:/Downloads/pythoncdc-main/scripts/pyc_verify.py
   single <pyc> --source <产物.py>` 确认 failure；`dis` 原 vs 产找首分歧。
3. 探针定位判据（monkeypatch + 逐块打印；region_analyzer 用 dis 必须**局部导入**）。
4. 写候选 spec：`{"file": "core/cfg/region_ast_generator.py", "edits":[{"anchor": LF 文本恰出现1次, "repl": "..."}]}`
   **repl 内嵌三要素注释（识别条件 / 归约方式 / AST 映射），标签 `[R71-thenover]`**。
   判据必须是同层次结构身份：无函数名/文件名/偏移常量/阈值启发、无名字白名单、无新增 self 状态、
   无跨层 `region.entry in r.blocks` 型模式。
5. 验证闭环 a–e（每条候选全过才算成立），与 fix1 同规：
   a. `python -X utf8 mbuild71.py <臂> specs/<候选>.json`（锚点断言全过）；
   b. 靶支：`h62.py run --arm=<臂> --list=<靶清单> --out=dump/<x>_<臂>.jsonl` 官方读数**逐项不变或改善**、
      `ab` 对 landed `REGRESSION=0`；mandated `pyc_verify.py single` 失败单元**清零或减少且零新增**；
   c. **金丝雀（本族最高风险）**：`fly/common/market_time.pyc` sha `af77224b34b203c4`、
      `IQCommon/util/datetime_func.pyc` `e711b8ea86d49a15`、`IQData/utils/datetime_func.pyc`
      `9d09af09249da177`、`fly/data/quotation.pyc` `4d41187e356544e0` —— 4 支产物 sha 必须与 R70
      逐字节相同（h62 口径 sha）；quotation 官方 143/143 维持。**若金丝雀 sha 变动，整件候选作废**
      （除非法动后金丝雀读数仍逐字节相同——那就说明你没动到它，正常）；
      额外逐字节自检：quotation / market_time 产物文本与 landed 的 `cmp` 必须为空。
   d. 电池：`python -X utf8 closeout69.py battery landed <臂>` worse-than-landed=0；
   e. 严格尺：`python -X utf8 sstrict67.py build_<臂> <靶清单> dump/strict_<臂>.json` 无新增缺陷函数。
6. 合成咬合：至少 3 支 synth（t01/t02/t22）在你的臂上转 `status=success` 或失败单元下降，
   且**负对照**（不触发该族的 synth，如 t03/t04）读数不变。

## 2. 硬约束

- **不修改 repo 任何文件**；禁止 402 全量扫描；每条命令 <300s。
- land71 只可 dry-run。
- h62 list 文件 LF 无 BOM、跑前删旧 jsonl；PowerShell 重定向是 UTF-16，一律 python 侧写文件。
- ADR-1：缺失/过冲族 Σ|Δ| 净减且不得以少发射换；位移族 hunk 严格降 + first_diff 回移 +
  Σ|Δ| 不升 + 严格尺不得新增 target_diff；**任何他支回归即整件拒收**。
- 宁缺毋滥：若放宽 guard 必然破坏金丝雀，则收窄到能同时通过的最小同层判据，或交付 `NONE` 结论
  （写明为什么不可修、需要什么配套）。

## 3. 交付

- `specs/<候选>.json`（每候选一份 + anchor 自检输出）
- `FACTS.md`：根因复核、判据三要素、a–e 读数、金丝雀逐字节比对、候选/拒绝清单、合成咬合
- `synth/*.py`（若新增）
- 最终回复：候选名 → 编辑处数 → a–e 结论 → 官方靶支读数变化 → 金丝雀 sha → 是否建议中心采纳。

不要 git commit/push（中心统一做）。逐步可验证，禁止投机取巧。
