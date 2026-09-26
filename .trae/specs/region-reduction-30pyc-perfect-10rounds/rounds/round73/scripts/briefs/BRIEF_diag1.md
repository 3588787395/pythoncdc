# R73 · diag1（测试工程师，只读诊断）BRIEF

## 0. 使命

Round 72 落地后 mandated ruler（`F:/Downloads/pythoncdc-main/scripts/pyc_verify.py`，
pylingual `compare_pyc`）给出 41 支 failure、**84 个 Different control flow + 4 个 Different
bytecode = 88 单元**。R72 diag1 已给出 108 单元的族聚类与判据行
（`rounds/round72/batches/diag1/FACTS.md`），R72 已清 F-EXTRA 与 F-OTHER genexpr 两族。
你的使命：**只读诊断头部文件，把剩余 88 单元重新聚类核实，补齐 R72 缺口的最小复现，
产出三要素判据提案**。**不写 patch，不改 repo。**

工作区：`D:/Temp/opencode/r73gate/diag1`（仪器已按本目录 ROOT 重定向）。
基线：HEAD = **R72 提交 `8d136040`**，h62 `--arm=landed` = repo（R72 字节）。

## 1. 输入数据

- `filecat.json`：41 支 failure 的逐支数据（official/pylingual 读数、类别计数、失败单元明细串）。
- `targets.md`：头部清单 + 四批分组；`G3v_pycverify_r72.json`：R72 全量报告。
- R72 交接 FACTS：`F:/Downloads/pythoncdc-main/.trae/specs/region-reduction-30pyc-perfect-10rounds/
  rounds/round72/batches/diag1/FACTS.md`（每族判据行 + synth 复现读数，行号以 R73 HEAD 重核）。
- 产物在 repo `site-packages/**/*OK.py`；官方尺/严格尺/mandated 单支仪器同前轮。

## 2. 诊断对象（units_failed 降序，A 组必做）

- **A 组（头部）**：`trade_live_broker`(14 cf)、`fly/data/quote`(12：cf10 + Different 2)、
  `trade_info_utils`(5 cf，**R70 遗留 `trade_operation target_diff #94` 仍在这支，必须给出到行根因**)、
  `real_quote`(4 cf)、`klinedata`(3)、`finance`(3)、`wizard_quant_api`(3，含 2 个 `<genexpr>`)、
  `bar`(3，limit_up/limit_down = F-TERNARY、_history_bars = F-ABSORB)、`order_api`(3)。
- **B 组（对照聚类）**：cf=1 长尾 26 支（`commission` 的 Different bytecode 1、`api_base` 两支
  各 1、`quotation.change_his_to_forward` 金丝雀单元等）——**只聚类、不动手**，用于判断族
  边界是否与 fix1/fix2/fix3 撞车，逐支标注归属族与建议归属批次。

## 3. 重点（R72 缺口，优先于新聚类）

1. **F-OTHER quote 2 支仍无最小复现**（R72 synth b07 外层 if 掏空、b08 `not in` 会员判据
   均 success 未触发）：`quote.check_industry_code`（`ra-gen :88-100 _flip_contains_compare`
   调用点 `:12743/:16032/:16386/:16823`，首分歧 `idx158 CONTAINS_OP in → not in`）与
   `quote.load_get_price`（`ra-gen :21530 _process_if_blocks`，`idx52 POP_JUMP_FORWARD_IF_FALSE
   → POP_TOP`）。**必须找到真实触发条件**（对齐原 pyc 行号/嵌套深度/elif 链形态）并产出复现。
2. **`trade_info_utils.trade_operation #94`**：R70 起连续 4 轮未修（读数
   `orig=('write_info',…) vs decomp=(None,'FOR_ITER')`）——给出首分歧指令 + 判据行 + 修复方向。
3. **F-PAD / F-ABSORB / F-POLARITY / F-TERNARY 在头部文件的落点重核**：fix1/fix2/fix3 正在
   并行打这四族，你的聚类表要标出**每支文件属于哪一族**（供中心裁定批次边界与合并顺序）。

## 4. 步骤

1. 对每支跑 `python -X utf8 F:/Downloads/pythoncdc-main/scripts/pyc_verify.py single <pyc>
   --source <OK.py>` 复现失败单元明细（含类别与行号/偏移前缀）。
2. 对失败单元 `dis` 原始 pyc vs 重编译产物的该 code object，找第一条分歧指令
   （跳转目标/极性/块结构/多余或缺失指令）。
3. 回溯 region_analyzer/generator 判据行（monkeypatch + 逐块打印探针）。
4. `synth/*.py` 最小复现 ≥10 支（**含第 3.1 条 F-OTHER quote 缺口至少 2 支**），
   编译 pyc 后用 `pyc_verify single` 验证 landed 复现同类别失败。
5. `FACTS.md`：每支靶的根因表（文件/单元/分歧指令/根因行号/族），每族三要素提案
   （识别条件/归约方式/AST 映射）与影响面，并标注「建议改 analyzer 还是 generator、
   大约几处编辑、归属哪一批」。

## 5. 硬约束

- **只读**：不修改 repo 任何文件、不提交；402 全量扫描禁止；每条命令 <300s。
- region_analyzer 无模块级 `import dis`——探针里必须局部导入（宽 except 吞 NameError 陷阱）。
- h62 list 文件 LF 无 BOM、跑前删旧 jsonl；PowerShell 重定向写 UTF-16，一律 python 侧写文件；
  `os.chdir` 破坏相对路径，传绝对 pyc 路径。
- 判据提案必须是同层次结构身份判据：无函数名/文件名/偏移/阈值启发、无名字白名单、
  无新增 self 状态、无跨层 `region.entry in r.blocks` 型模式。

## 6. 交付

- `FACTS.md`（根因表 + 族聚类 + 三要素提案 + 影响面 + 批次归属建议）；
- `synth/*.py` ≥10 支最小复现（附每支 landed 读数，R72 未复现的 2 支必须补上）；
- `specs/` 留空（不出 patch），但每族给出修改位置建议。
