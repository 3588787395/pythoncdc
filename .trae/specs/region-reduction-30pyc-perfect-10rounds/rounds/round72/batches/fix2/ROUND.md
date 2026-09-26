# R72 · round（Round 72 总纲 + diag1 只读诊断 BRIEF）

## 0. 使命与基线

Round 71 落地 m71 后，mandated ruler（`F:/Downloads/pythoncdc-main/scripts/pyc_verify.py`，
pylingual `compare_pyc`）对 402 支产物给出 **47 支 failure（85 个 Different control flow +
12 个 Different/Extra bytecode 单元）**，读数 **6515/6623 = 98.37%**；官方尺
5746/5717/99.50%（ok 394、partial 8、failed 0）。

- 起始 HEAD = **Round 71 提交 `6c0a8f8c`**；repo core = R71 字节
  （generator sha `6203253987adedcf`、analyzer sha `8ca47f7d6b9244cf`、comprehension `be5490c1118c7199`）。
- 本轮任务：**分三批并行**——diag1 只读诊断头部 cf 族；fix1 端到端打
  genexpr/listcomp Different bytecode 族（`comprehension_generator.py` 至今未改过）；
  fix2 端到端打头部 control-flow 族。中心统一 ADR-1 复测、合并、落地、门禁、归档、提交 push。

## 1. 通用输入（三工作区各有一份）

- `filecat.json`：47 支 failure 的逐支数据（official/pylingual 读数、类别计数、失败单元明细串）。
- `targets.md`：头部 16 支 + 三批分组与逐支 failure 明细。
- `G3v_pycverify_r71.json`：R71 全量报告（rows 含完整 failures）。
- 产物在 repo：`site-packages/**/*OK.py`（18 支 R71 变更已出货）。

## 2. diag1（测试工程师，只读）—— 头部 cf 聚类

见 `briefs/BRIEF_diag1.md`。交付 `FACTS.md` + `synth/` ≥10 支最小复现 + 每族三要素提案。

## 3. 本轮硬纪律（三工作区通用）

- 只读 repo：**禁止**修改/提交/落地（`land72` 只可 dry-run 断言，禁止 `--apply`）；
  **禁止 402 全量扫描**（归中心）；每条命令 <300s。
- 调用任何子代理/开工前由中心本地提交；代理自报读数不采信，中心复测。
- region_analyzer 无模块级 `import dis`——探针里用 dis 必须局部导入（R67 陷阱）。
- h62 list 文件 LF 无 BOM、跑前删旧 jsonl；`os.chdir` 破坏相对路径，传绝对 pyc 路径；
  PowerShell 重定向写 UTF-16，一律 python 侧写文件。
- 判据提案必须是**同层次结构身份判据**：无函数名/文件名/偏移/阈值启发、无名字白名单、
  无新增 self 状态、无跨层 `region.entry in r.blocks` 型模式。
- 金丝雀 pin（产物 sha16，LF 归一）：market_time `af77224b34b203c4`、
  IQCommon datetime_func `e711b8ea86d49a15`、IQData datetime_func `9d09af09249da177`、
  quotation `3eb76e512df9ab1e`（官方必须维持 143/143、mandated 维持 152/153 不倒退）。

## 4. 批次一览

| 批 | 类型 | 对象（units_failed） | 工作区 |
|---|---|---|---|
| diag1 | 只读诊断 | trade_live_broker 15、quote 12、broker 7、trade_info_utils 5、real_quote 4、klinedata/bar/wizard/order_api/finance 各 3 | `r72gate/diag1` |
| fix1 | 候选 spec | genexpr/listcomp Different bytecode：future_position 4、live_future_position 4、option_position 2、asset_mixin 1 | `r72gate/fix1` |
| fix2 | 候选 spec | head cf：broker 7、quote 12、trade_live_broker 15、quotation 1（金丝雀单元，只作对照） | `r72gate/fix2` |
