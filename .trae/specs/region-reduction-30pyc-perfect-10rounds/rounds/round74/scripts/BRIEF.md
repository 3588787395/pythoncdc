# R74 · 任务书（BRIEF.md）— 35 支失败 pyc / 77 单元，四批并行攻坚

## -1. 用户裁定（最高优先级，继承 R73 commit `b355043e`，不得推翻）

**用户明确指认：剩余控制流失败的根因就是「嵌套 try-except 问题」。**
本轮对该裁定的**中心定量读数（据实入档、不捏造）**（`center/dump/` 的
`firstdiv73.txt` / `tryverdict73.txt` / `crosstab74.txt`，汇总 `center/logs/TRYVERDICT_r74.txt`）：

| 读数 | R74 基线（77 失败单元，76 个可探） |
|---|---|
| 原 pyc **有**异常表 / **无**异常表 | **39 / 37** |
| 异常表逐字节相同 `et_same` / 有差 `et_diff` | **49 / 27** |
| 产品异常表比原表更深 `prod_deeper` | **0**（嵌套深度差 0 项） |
| **首分歧在异常区内 / 区外** | **11 / 65** |

⇒ 裁定对 **11 单元的 inside-try 子族成立**（fix3 主战场，本批按裁定全力打）；
对其余 65 单元**定量上不成立**，须以同层次判据另解（fix1/fix2 承担）。
两组读数并列存档，保留分歧而不掩盖；**不改尺、不以少发射换取全绿**。

## 0. 使命与基线

- 基线 HEAD = **R73 提交 `6bb9716a`**（mandated `6540/6617 = 98.84%`，35 支 failure、77 失败单元；
  官方 `5717/5746 = 99.50%`；严格尺缺陷 75；金丝雀 4/4 pin 不变）。
- 每批产出**候选 patch spec 并在镜像上闭环自证**（只读 repo、禁落地），按子机制**单臂单 edit 拆开自证**（ADR-1）。
- **本轮 mandate：≥1 支 pyc failure → success**。已知最短路径三条：
  1. fix1（abs1+abs2 合并）→ `IQCommon/data/local_finance.pyc` 20/21 → **21/21**（R73 实测 +4 单元）；
  2. fix3（inside-try 族）→ `IQData/…/real_quote.pyc` 41/45 → 45/45（4 失败单元中 3 个在异常区内）；
  3. fix2+fix1 合并（中心裁）→ `IQCommon/util/trade_info_utils.pyc` 36/41 → 41/41（3 F-PAD + 2 F-ABSORB）。

## 1. 家族地图（R74 中心实测：`fam74_r74.json`，77 单元按真尺 verdict 聚类）

| 家族 | 单元数 | 异常区外 OUT | 异常区内 IN | 主战场文件 |
|---|---|---|---|---|
| **F-ABSORB** | **67** | 58 | **9** | trade_live_broker 12、quote 8、real_quote 4、wizard_quant_api/finance/klinedata/order_api 各 3 |
| **F-PAD** | **8** | 6 | **2** | trade_info_utils 3、quote 2、flytools 1、function 1、trade_live_broker 1 |
| **F-POLARITY** | 1 | 1 | 0 | trade_live_broker `_sync_worker` |
| **F-OTHER** | 1 | 1 | 0 | quote `load_get_price` |

失败单元分布（35 支）：trade_live_broker 14、quote 11、trade_info_utils 5、real_quote 4、
wizard_quant_api/finance/klinedata/order_api 各 3、jq_trans_module/future_contract_info/
risk_calculation/ptradeAccount 各 2，其余 19 支各 1（明细 `filecat.json` / `fail74.txt`）。

## 2. R73 交接（直接决定本轮 fix1 走向）

- **候选 abs1**（`_is_nested_if_else_pattern` same-target 豁免，spec `r73gate/fix2/specs/abs1_nested_same_exit.json`）
  **未落地**（landed 无该分支）：R73 实测 mandated 41 靶 +4 单元、
  `local_finance` failure→success、official Σ|Δ| 186→185、battery worse=0、strict 缺陷 79→75 NEW=0。
- **但合并臂 absm 被 ADR-1 拒收**：klinedata `get_multiminute_his_data` 产品**丢 1 条尾语句**
  （`his_data_dict = get_kline_by_count_new(…)`，−11 指令，strict seq_len 482→471）＝「以少发射换」。
- **中心给定方向 = `abs2`**：问题成因是「共享尾 region 合并后，`Region@2710` 成 child 但不在
  `blocks/then_blocks` → 生成器跳过 → 语句丢失」（`r73gate/fix2/FACTS.md §2/§5`）。
  ⇒ fix1 必须在 **`region_ast_generator` 侧补 orphan child region 发射**，再与 abs1 合臂复测
  （收益保留 + 尾语句恢复，ADR-1 WORSE=0 才可交中心落地）。

## 3. 批次分工

| 批 | 主攻 | 交付 |
|---|---|---|
| **diag1** | 只读：67 F-ABSORB 单元子机理归属（same-target 共享 else / orphan-child 丢语句 / 其他）+ 11 inside-try 逐行根因 | `FACTS.md` + `dump/` 探针（不出 spec） |
| **fix1** | **abs2（generator orphan child 发射）** + abs1 合臂 `absj` | `specs/abs2*.json`、`specs/absj.json` + 闭环读数 |
| **fix2** | **F-PAD 8 + F-POLARITY 1 + F-OTHER 1**（10 单元） | 每 edit 单臂 spec + 闭环读数 |
| **fix3** | **inside-try 11 单元**（按用户裁定的 try-except 归约路径） | 每 edit 单臂 spec + 闭环读数 |

重叠仲裁：同一单元可能被多批命中（如 quote `run_tick_socket` = F-PAD 且 IN；trade_live_broker
多单元 = F-ABSORB 且被判据重叠）。**批次不得跨判据点自合并**，全部标注重叠面交中心
（`adr74.py` 同尺复测）裁定；中心合并臂唯一、落地唯一。

## 4. 硬规则（每批必守）

1. **不改 repo 任何文件**（`F:/Downloads/pythoncdc-main` 全程只读；`land74` 只许 dry-run，禁 `--apply`）；
   禁手改任何 `*OK.py`；402 全量扫描禁止在批内做（归中心）。
2. 每条命令 **<300s**；大活拆分片；`dis`/region 侧探针**局部导入**（避 try 外 NameError）。
3. 镜像闭环用本工作区工具：`mbuild74.py <arm> specs/<x>.json`（锚点必须 LF 归一后恰出现 1 次）→
   `h62.py run --arm=<arm> --list=…`（官方读数）→ `python -X utf8 …/scripts/pyc_verify.py single <pyc>
   --source build_<arm>/<产物>`（mandated）→ `closeout69.py battery landed <arm>`（worse=0）→
   `sstrict67.py build_<arm> <名单> <out>`（无新增缺陷）。
4. **金丝雀 4 支 sha16 不得变**：quotation `3eb76e512df9ab1e`、market_time `af77224b34b203c4`、
   IQCommon datetime_func `e711b8ea86d49a15`、IQData datetime_func `9d09af09249da177`。
5. **ADR-1**：任何他支回归即整件拒收；**不得以少发射换**（少一条语句/少一个 load 即 WORSE）；
   位移族要 hunk 严格子集 + first_diff 回移 + Σ|Δ| 不升。
6. spec 三要素注释（识别条件 / 归约方式 / AST 映射）；同层次结构身份判据：无函数名、无文件名、
   无偏移阈值、无名字白名单、无新增 self 状态、无跨层 `region.entry in r.blocks` 型模式。
7. 产物名带 `:` 时 `mbuild`/`h62` 用 `.replace(':','_')`；h62 列表文件 LF 无 BOM、跑前删旧 jsonl。
8. 每批结束写 `FACTS.md`（读数表 + 与他批重叠面 + 原始 jsonl 索引），spec 放 `specs/`，复现放 `synth/`。

## 5. 输入清单（每工作区已就位）

- `filecat.json`（35 文件/77 单元明细）、`fail74.txt`、`fam74_r74.json`（家族判定）、
  `dump/crosstab74.txt`（家族×异常区交叉表）、`G3v_pycverify_r73.json`（基线 G3v）。
- 工作区：`D:/Temp/opencode/r74gate/{diag1,fix1,fix2,fix3,center}`（工具已从 r73gate 中心件重定向）。
- 中心件：`adr74`（=`adr73.py`，内容已重定向）、`gates74.py`、`merge_g3v74.py`、`land74.py`、
  `mkfinal74.py`、`mkmirr_prev74.py`、`mkarchive74.py`、`tryverdict_summary74.py`。
