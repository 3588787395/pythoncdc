# R72 · diag1（测试工程师，只读诊断）BRIEF

## 0. 使命

Round 71 落地后 mandated ruler（`F:/Downloads/pythoncdc-main/scripts/pyc_verify.py`，
pylingual `compare_pyc`）给出 47 支 failure、**85 个 Different control flow 单元**（头部 10 支占
大半）+ 12 个 Different/Extra bytecode 单元。你的使命：**只读诊断头部 cf 文件**，把失败单元
按**结构性族**聚类，定位 `core/cfg/region_analyzer.py` / `region_ast_generator.py` 的根因
（到行号），产出 **≥10 支最小复现**与三要素判据提案。**不写 patch，不改 repo。**

工作区：`D:/Temp/opencode/r72gate/diag1`（仪器已按本目录 ROOT 重定向）。
基线：HEAD = **R71 提交 `6c0a8f8c`**，h62 `--arm=landed` = repo（R71 字节）。

## 1. 输入数据

- `filecat.json`：47 支 failure 的逐支数据（official/pylingual 读数、类别计数、失败单元明细串）。
- `targets.md`：头部 16 支 + 分批说明；`G3v_pycverify_r71.json`：R71 全量报告。
- 产物在 repo `site-packages/**/*OK.py`；官方尺/严格尺/mandated 单支仪器同 R71。

## 2. 诊断对象（units_failed 降序，A 组必做）

- **A 组（头部）**：`trade_live_broker`(15：cf13 + Different 1 + Extra 1)、
  `fly/data/quote`(12：cf10 + Different 2)、`simulation/broker`(7：Extra 4 + Different 2 + cf1)、
  `trade_info_utils`(5 cf，R70 遗留 `trade_operation target_diff #94` 正在这支)、
  `real_quote`(4 cf)、`klinedata`(3 cf)、`bar`(3 cf)、`wizard_quant_api`(3 cf)、
  `order_api`(3 cf)、`finance`(3 cf)。
- **B 组（对照聚类）**：cf=1 长尾 28 支与 genexpr/listcomp bytecode 族（position_model 三支 +
  `asset_mixin`，由 fix1 并行攻坚）——**只聚类、不动手**，用于判断族边界是否与 fix1 撞车。

## 3. 步骤

1. 对每支跑 `python -X utf8 F:/Downloads/pythoncdc-main/scripts/pyc_verify.py single <pyc>
   --source <OK.py>` 复现失败单元明细（含类别与行号/偏移前缀）。
2. 对失败单元 `dis` 原始 pyc vs 重编译产物的该 code object，找第一条分歧指令
   （跳转目标/极性/块结构/多余或缺失指令）。
3. 回溯 region_analyzer/generator 判据行（monkeypatch + 逐块打印探针）。
4. `synth/*.py` 最小复现 ≥10 支，编译 pyc 后用 `pyc_verify single` 验证 landed 复现同类别失败。
5. `FACTS.md`：每支靶的根因表（文件/单元/分歧指令/根因行号/族），每族三要素提案
   （识别条件/归约方式/AST 映射）与影响面（还有哪些文件同族），并标注「建议改 analyzer 还是
   generator、大约几处编辑」。

## 4. 硬约束

- **只读**：不修改 repo 任何文件、不提交；402 全量扫描禁止；每条命令 <300s。
- region_analyzer 无模块级 `import dis`——探针里必须局部导入（宽 except 吞 NameError 陷阱）。
- h62 list 文件 LF 无 BOM、跑前删旧 jsonl；PowerShell 重定向写 UTF-16，一律 python 侧写文件；
  `os.chdir` 破坏相对路径，传绝对 pyc 路径。
- 判据提案必须是同层次结构身份判据：无函数名/文件名/偏移/阈值启发、无名字白名单、
  无新增 self 状态、无跨层 `region.entry in r.blocks` 型模式。

## 5. 交付

- `FACTS.md`（根因表 + 族聚类 + 三要素提案 + 影响面）；
- `synth/*.py` ≥10 支最小复现（附每支 landed 读数）；
- `specs/` 留空（不出 patch），但每族给出修改位置建议。
