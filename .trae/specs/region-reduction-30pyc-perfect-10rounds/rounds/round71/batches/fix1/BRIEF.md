# R71 · fix1（修复工程师）BRIEF

## 0. 使命

mandated ruler（`F:/Downloads/pythoncdc-main/scripts/pyc_verify.py`，pylingual `compare_pyc`）
在 402 支产物上给出 56 支 failure（Different control flow 102 / Different bytecode 17 /
Extra bytecode 6；48 支官方 ok 的「分歧集」）。diag1（测试工程师，并行工作中）负责重 cf≥2
文件与族聚类；**你负责：从 B 组（cf=1 长尾 + cf=0 Different-bytecode）里挑 1–3 个最能钉死的族，
端到端产出候选 patch spec 并在镜像上验证**。不碰 repo、不落地。

你的工作区：`D:/Temp/opencode/r71gate/fix1`（仪器已按本目录 ROOT 重定向）。
基线：HEAD = R70 落地 `b21c5c61`；h62 `--arm=landed` = repo（R70 字节）。


## 0.5 用户实测线索（最高优先假设）

**用户明确提示：多数是嵌套 try-except 问题。** 请把「嵌套 try/except 的区域归约与发射」
作为第一假设：
- region_analyzer 的 TryRegion 识别（嵌套 try 时的块归属、handler 区间、异常表隐式边）；
- region_ast_generator 的 try/except/finally 发射（嵌套时 except 臂与外层 try 的边界、
  SETUP_FINALLY/POP_EXCEPT 配对、`except ... as e` 的 e 作用域块）；
- pylingual 失败类别里 Missing/Extra bytecode 与 Different control flow 在嵌套 try 场景的
  典型表现：POP_EXCEPT 位置、异常臂尾 JUMP_FORWARD 落点、finally 的重复发射。
线索需**实测验证**：先确认靶支失败单元确实位于嵌套 try 结构内（dis + 反汇编对照），
再回溯判据行；不要先入为主硬套。

## 1. 输入数据

- `filecat.json`：56 支 failure 的逐支数据（失败类别计数 + 每支前 40 条 failure 明细串，
  串里含 pylingual 前缀命名的失败单元名与类别）。
- `G3v_pycverify_r70.json`：全量报告。

## 2. 建议优先族（从 filecat.json 自己核实）

- **position_model 族（cf=0，Different bytecode 4/4/2）**：
  `future_position` pyl 79/83、`live_future_position` 71/75、`option_position` 65/67 ——
  三支同目录同族，Different bytecode 计数同构，大概率一条判据清三支。
- **cf=1 长尾同签名聚类**：`exception.pyc`×3（IQCommon/IQData/IQEngine 的 pyl 都比官方多 1
  且 cf=1）、account_model 四支（benchmark_account/stock_account/stock_position/order?）、
  `executor`/`slippage`/`strategy_universe`（IQEngine/core 小文件）、`entry`/`calexrights`×2、
  `cgroup_utils`/`email_utils` —— 先按失败单元名聚类，挑最大同构族。
- **Extra bytecode 支**：`simulation/broker`（Extra 4 + Different bytecode 2，pyl 35/42）、
  `simulation/live`（Extra 1）—— 多发射族，修复方向是削减发射（注意 ADR-1 第 1 条）。

## 3. 步骤

1. 聚类：从 `filecat.json` 提取失败单元名与类别，挑 1–3 个同构族。
2. 复现：对族内每支跑 `python -X utf8 F:/Downloads/pythoncdc-main/scripts/pyc_verify.py single
   <pyc> --source <OK.py>`，`dis` 对比失败单元，定位分歧指令。
3. 根因到行：region_analyzer / region_ast_generator 判据行（monkeypatch 探针法）。
4. 写 spec：`{"file": "core/cfg/<x>.py", "edits": [{"anchor": LF 文本恰出现 1 次, "repl": ...}]}`
   —— **repl 内嵌三要素注释（识别条件/归约方式/AST 映射）**；同层次结构身份判据：无函数名/
   文件名/偏移/阈值启发、无名字白名单、无新增 self 状态、无跨层 `region.entry in r.blocks` 型模式。
5. 验证闭环（每条候选）：
   a. `python -X utf8 mbuild71.py <臂名> specs/<候选>.json`（锚点断言必须全过）；
   b. 靶支：h62 `run --arm=<臂名>` 官方读数**逐项不变或改善**（不得回退）+ mandated
      `pyc_verify.py single <pyc> --source <build_<臂名>产物>` 失败单元**清零或减少且零新增**；
   c. 金丝雀：market_time / 两支 datetime_func 产物 sha 与 R70 逐字节相同
      （`af77224b34b203c4` / `e711b8ea86d49a15` / `9d09af09249da177`）；quotation 官方 143/143
      必须维持（其 sha 若动，仅允许是其 2 个 cf 单元真实转绿）；
   d. 电池：`python -X utf8 closeout69.py battery landed <臂名>` worse-than-landed=0；
   e. 严格尺：`python -X utf8 sstrict67.py build_<臂名> <名单> <out>` 无新增缺陷函数。
   （b–e 的原始输出存 `dump/`，供中心复核。）

## 4. 硬约束

- **不修改 repo 任何文件**（land71 只可 dry-run 断言，禁止 --apply）；402 全量扫描禁止。
- 每条命令 <300s；region_analyzer 里用 dis 必须局部导入（宽 except 吞 NameError 陷阱）。
- h62 list 文件 LF 无 BOM、跑前删旧 jsonl；sstrict67 第一参数是本工作区 `build_<arm>`。
- ADR-1：缺失/过冲族（seq_len）要求 Σ|Δ| 净减且不得以少发射换；位移族（counts 相等）要求
  hunk 严格降 + first_diff 回移 + Σ|Δ| 不升；**任何他支回归即整件拒收**。

## 5. 交付

- `FACTS.md`（族聚类、根因表、每候选的 a–e 验证读数）；
- `specs/*.json`（每候选一份，anchor 断言自检打印）；
- `synth/*.py` 最小复现（若有）。
