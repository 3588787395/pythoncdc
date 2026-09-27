# R73 · round（Round 73 总纲 + diag1 只读诊断 BRIEF）

## 0. 使命与基线

Round 72 落地 m72（comprehension_generator 4 edits/+99）后，mandated ruler
（`F:/Downloads/pythoncdc-main/scripts/pyc_verify.py`，pylingual `compare_pyc`）对 402 支产物
给出 **41 支 failure（84 个 Different control flow + 4 个 Different bytecode 单元 = 88 单元）**，
读数 **6529/6617 = 98.67%**；官方尺 5746/5717/99.50%（ok 394、partial 8、failed 0）。

- 起始 HEAD = **Round 72 提交 `8d136040`**；repo core = R72 字节
  （generator sha `6203253987adedcf`、analyzer sha `8ca47f7d6b9244cf`、
  comprehension sha `b432a35580989852`）。R72 已清 F-EXTRA 全族与 F-OTHER genexpr 全族。
- 本轮任务：**分四批并行**——diag1 只读诊断头部；fix1 端到端打 **F-PAD**（14 单元，
  落点一律 +4）；fix2 端到端打 **F-ABSORB 主体**（70 单元最大族）；fix3 打 **手术族**
  （F-TERNARY 2 + F-POLARITY + F-EXCTABLE 1 + F-OTHER quote 2）。中心统一 ADR-1 复测、
  合并、落地、门禁、归档、提交 push。**Mandate：至少 1 支 pyc failure → success。**

## 1. 通用输入（四工作区各有一份）

- `filecat.json`：41 支 failure 的逐支数据（official/pylingual 读数、类别计数、失败单元明细串）。
- `targets.md`：头部清单 + 四批分组与逐支 failure 明细。
- `G3v_pycverify_r72.json`：R72 全量报告（rows 含完整 failures）。
- 产物在 repo：`site-packages/**/*OK.py`（R72 已出货 11 支变更）。
- R72 diag1 交接：`rounds/round72/batches/diag1/FACTS.md`（108 单元族聚类、每族判据行、
  synth 复现读数）——**本轮判据行行号以 R73 HEAD 实测为准**（comprehension_generator 已变，
  region_analyzer / region_ast_generator 未变、行号沿用）。

## 2. diag1（测试工程师，只读）—— 头部聚类 + 缺口复现

见 `briefs/BRIEF_diag1.md`。交付 `FACTS.md` + `synth/` ≥10 支最小复现 + 每族三要素提案。

## 3. 本轮硬纪律（四工作区通用）

- 只读 repo：**禁止**修改/提交/落地（`land73` 只可 dry-run 断言，禁止 `--apply`）；
  **禁止 402 全量扫描**（归中心）；每条命令 <300s。
- 调用任何子代理/开工前由中心本地提交；代理自报读数不采信，中心复测。
- region_analyzer 无模块级 `import dis`——探针里用 dis 必须局部导入（R67 陷阱）。
- h62 list 文件 LF 无 BOM、跑前删旧 jsonl；`os.chdir` 破坏相对路径，传绝对 pyc 路径；
  PowerShell 重定向写 UTF-16，一律 python 侧写文件。
- 判据提案必须是**同层次结构身份判据**：无函数名/文件名/偏移/阈值启发、无名字白名单、
  无新增 self 状态、无跨层 `region.entry in r.blocks` 型模式。
- **镜像臂名前缀按批隔离**（四批并发建镜像）：fix1 只用 `pad*`、fix2 只用 `abs*`、
  fix3 只用 `surg*`（例 `mbuild73.py pad1 specs/xxx.json` → `mirr_pad1` / `build_pad1/`）。
- 金丝雀 pin（产物 sha16，LF 归一）：market_time `af77224b34b203c4`、
  IQCommon datetime_func `e711b8ea86d49a15`、IQData datetime_func `9d09af09249da177`、
  quotation `3eb76e512df9ab1e`（官方必须维持 143/143、mandated 维持 152/153 不倒退）。

## 4. 批次一览（units_failed 取自 round72 G3v）

| 批 | 类型 | 族（R72 diag1 交接） | 主攻对象 | 工作区 |
|---|---|---|---|---|
| diag1 | 只读诊断 | 头部聚类 + 缺口复现 | trade_live_broker 14、quote 12、trade_info_utils 5、real_quote 4、klinedata/finance/wizard/bar/order_api 各 3 | `r73gate/diag1` |
| fix1 | 候选 spec | **F-PAD** 14（落点一律 +4） | 全 filecat 扫 `+4` 特征签名，逐支定位 ra-gen :185 / :26482 / :14865 | `r73gate/fix1` |
| fix2 | 候选 spec | **F-ABSORB** 70（and 链共享 else / 链尾吸收） | trade_live_broker、quote、trade_info_utils、real_quote 等头部 cf | `r73gate/fix2` |
| fix3 | 候选 spec | F-TERNARY 2 + F-EXCTABLE 1 + F-POLARITY + F-OTHER quote 2 | bar、commission、api_base、quote（2 单元） | `r73gate/fix3` |

## 5. ADR-1 与验证闭环（每件候选）

a. `mbuild73.py <臂名> <spec>` 锚点断言全过；b. 靶支官方读数逐项不变或改善 + mandated
失败单元清零或减少且零新增；c. 金丝雀 4 支 sha 不变；d. `closeout69.py battery landed <臂名>`
worse-than-landed=0；e. `sstrict67.py build_<臂名> <名单> <out>` 无新增缺陷函数。
（b–e 原始输出存各自 `dump/`，中心复测不采信自报。）**任何他支回归即整件拒收**。
