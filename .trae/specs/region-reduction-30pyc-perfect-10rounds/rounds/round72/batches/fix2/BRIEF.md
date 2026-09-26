# R72 · fix2（修复工程师）BRIEF —— 头部 control-flow 族

## 0. 使命

mandated ruler 剩余 47 支 failure 里，头部 control-flow 族占 85 个 cf 单元的大半。
你的使命：**挑一个可端到端钉死的族，产出候选 patch spec 并在镜像上验证**（不碰 repo、
不落地），目标之一是让某支 pyc 从 failure 变 **success（完全 OK）**。

工作区：`D:/Temp/opencode/r72gate/fix2`；基线 HEAD = **R71 提交 `6c0a8f8c`**，
h62 `--arm=landed` = repo（R71 字节）。

## 1. 输入数据

- `filecat.json`（47 支 failure 明细）、`targets.md`、`G3v_pycverify_r71.json`。

## 2. 建议优先族（从 filecat.json 自己核实）

- **首选 `simulation/broker.pyc`（7 单元 = Extra bytecode 4 + Different bytecode 2 + cf 1，
  官方 24/24 ok、pylingual 35/42）**：混合族，全清即该支 failure→success（mandate 最短路径）；
  Extra bytecode 方向是**削减发射**（注意 ADR-1 不得以少发射换）。
- **次选 `real_quote.pyc`（4 cf，官方 40/44、pylingual 41/45）** 或 `finance.pyc`(3 cf)、
  `klinedata.pyc`(3 cf)：同为官方 ok 的分歧集，族更单纯。
- `fly/data/quote.pyc`（cf10 + Different 2）与 `trade_live_broker.pyc`（cf13 + 各 1）：
  体量大；**R70 diag2 对 quote 的 T1/T3 拆臂已被 ADR-1 证伪回退**，若你碰 quote，
  必须先拆臂自证（T1/T3 各自单独跑）再谈采纳。
- `fly/data/quotation.pyc`（金丝雀，1 cf 单元 `change_his_to_forward`）：**只作对照**，
  打它需中心裁定；任何情况官方必须维持 143/143、mandated 不得低于 152/153。

## 3. 步骤

1. 聚类：从 `filecat.json` 提取失败单元名与类别，挑 1 个同构族（建议 broker 或 real_quote）。
2. 复现：`python -X utf8 F:/Downloads/pythoncdc-main/scripts/pyc_verify.py single <pyc>
   --source <OK.py>`；`dis` 对比失败单元，找第一条分歧指令（跳转目标/极性/块结构/多余指令）。
3. 根因到行：region_analyzer / region_ast_generator 判据行（monkeypatch 探针法）。
4. 写 spec：`{"file": "core/cfg/<x>.py", "edits": [{"anchor": LF 文本恰出现 1 次, "repl": ...}]}`
   —— **repl 内嵌三要素注释（识别条件/归约方式/AST 映射）**；同层次结构身份判据：
   无函数名/文件名/偏移/阈值启发、无名字白名单、无新增 self 状态、无跨层
   `region.entry in r.blocks` 型模式。
5. 验证闭环（每条候选）：
   a. `python -X utf8 mbuild72.py <臂名> specs/<候选>.json`（锚点断言必须全过）；
   b. 靶支：h62 `run --arm=<臂名>` 官方读数**逐项不变或改善**（不得回退）+ mandated
      `pyc_verify.py single <pyc> --source <build_<臂名>产物>` 失败单元**清零或减少且零新增**；
   c. 金丝雀：market_time `af77224b34b203c4`、datetime_func `e711b8ea86d49a15` /
      `9d09af09249da177`、quotation `3eb76e512df9ab1e` 四支 sha 与 R71 逐字节相同
      （quotation 若动，仅允许其 cf 单元真实转绿且官方 143/143 维持）；
   d. 电池：`python -X utf8 closeout69.py battery landed <臂名>` worse-than-landed=0；
   e. 严格尺：`python -X utf8 sstrict67.py build_<臂名> <名单> <out>` 无新增缺陷函数。
   （b–e 原始输出存 `dump/`，供中心复核。）

## 4. 硬约束

- **不修改 repo 任何文件**（`land72` 只可 dry-run 断言，禁止 `--apply`）；402 全量扫描禁止。
- 每条命令 <300s；region_analyzer 里用 dis 必须局部导入（宽 except 吞 NameError 陷阱）。
- h62 list 文件 LF 无 BOM、跑前删旧 jsonl；sstrict67 第一参数是本工作区 `build_<arm>`。
- ADR-1：缺失/过冲族（seq_len 类）要求 Σ|Δ| 净减且不得以少发射换；位移族（counts 相等）
  要求 hunk 严格降 + first_diff 回移 + Σ|Δ| 不升；**任何他支回归即整件拒收**。
- 与 diag1 并行：diag1 正在只读诊断同一批头部文件，你的 spec 若与其根因表冲突，
  在 FACTS 里如实标注分歧点，交中心裁定。

## 5. 交付

- `FACTS.md`（族聚类、根因表、每候选 a–e 验证读数，quote 若碰须附拆臂读数）；
- `specs/*.json`（每候选一份，anchor 断言自检打印）；
- `synth/*.py` 最小复现（若有）。
