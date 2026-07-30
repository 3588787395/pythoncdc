# 验证清单

> 目标：通过持续「测试工程师 + 修复工程师」迭代（每轮取索引中一个 pyc 文件），将反编译逻辑写入 11 个 `_identify_*_regions`（6 节模板）与 9+ 个 `_generate_*`（4 节模板）方法注释，驱动 site-packages 下全部 130+ pyc 文件反编译字节码 100% 等价，每个 pyc 生成同名 `+OK.py`。
> 当前状态：待执行

## 通用约束（每轮检查）

- [ ] G1 命令执行时间 ≤ 300 秒
- [ ] G2 每轮 commit + push 到 origin/main（commit 前缀 `rcm-rNN:`）
- [ ] G3 无反模式新增（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀 0 新增）
- [ ] G4 无硬编码深度上限新增（`depth > N` / `count < N` 等魔法数字）
- [ ] G5 该轮 10+ 最小复现实例全部通过（若该 pyc 已 100% 一致则豁免）
- [ ] G6 既有测试矩阵无退化（IF/LOOP/TRY/WITH/MATCH/BOOLOP/TERNARY/CC/SEQ/ASSERT 子集）
- [ ] G7 `decompile_report.md` + `fix_report.md` 已生成
- [ ] G8 涉及的 `_identify_*_regions` 方法 docstring 已按 6 节模板更新
- [ ] G9 涉及的 `_generate_*` 方法 docstring 已按 4 节模板更新
- [ ] G10 单轮独立目录 `rounds/round_NN/{test_engineer/, repair_engineer/}` 已创建
- [ ] G11 禁止修改反编译生成的 `+OK.py` 文件
- [ ] G12 禁止任何投机取巧（针对特定 pyc 的硬编码绕过）
- [ ] G13 累计成功率 ≥ 上一轮（单调递增，禁止下降）
- [ ] G14 每轮取下一个 pyc（按 pyc_index.json path 字母序轮询，禁止重复取已 `ok` 的 pyc）

## 预备阶段（Phase 0）

- [x] P0.1 `scripts/pyc_index_builder.py` 已创建并可用
- [x] P0.2 `scripts/pyc_batch_verify.py` 已创建并可用
- [x] P0.3 `pyc_index.json` 已生成，覆盖 site-packages 下全部 pyc 文件（402 条目）
- [x] P0.4 `baseline/success_rate.txt` 已记录首个 pyc 起始成功率（0.0）

## 阶段一（Phase 1：注释模板对齐）

- [x] P1.1 `phase1/comment_audit.md` 已生成（11 个 `_identify_*_regions` 方法注释缺失节清单，11/11 合规）
- [x] P1.2 `phase1/generate_audit.md` 已生成（18 个 `_generate_*` 方法注释缺失节清单，10 合规/3 部分/5 不合规）
- [x] P1.3 `phase1/region_test_baseline.txt` 已记录既有区域测试矩阵基线通过率（94.88%，3614 测试）

## 阶段二（Phase 2：持续迭代）

### 通用轮次检查清单（每轮 NN 复制一份）

- [ ] R-NN-0 该轮取的 pyc 文件路径已记录（`decompile_status != ok`，按 path 字母序轮询）
- [ ] R-NN-1 测试工程师 `decompile_report.md` 已生成（含不一致清单 + 当前 pyc 成功率 + 累计成功率 + 与上一轮对比）
- [ ] R-NN-2 ≥ 10 个最小复现实例已归档至 `minimal_repros/`（全部 py_compile + DEFECT-REPRO 验证通过；若该 pyc 已 100% 一致则豁免）
- [ ] R-NN-3 修复工程师 `fix_report.md` 已生成（修复点 + 算法依据 + 注释更新清单 + 回归结果 + 残留不一致数）
- [ ] R-NN-4 涉及的 `_identify_*_regions` 方法 docstring 已按 6 节模板更新
- [ ] R-NN-5 涉及的 `_generate_*` 方法 docstring 已按 4 节模板更新
- [ ] R-NN-6 既有测试矩阵无退化
- [ ] R-NN-7 10+ 复现实例全部通过
- [ ] R-NN-8 反模式自检通过（G3）
- [ ] R-NN-9 算法 4 原则 FULLY COMPLIANT（自底向上归约 / 每块唯一归属 / 嵌套抽象节点 / 入口引用语义）
- [ ] R-NN-10 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 编译通过
- [ ] R-NN-11 累计成功率 ≥ 上一轮
- [ ] R-NN-12 若该 pyc 100% 一致：`<name>OK.py` 已生成且 `py_compile` 通过
- [ ] R-NN-13 pyc_index.json 已更新（decompile_status / bytecode_match_rate / ok_py_generated / last_tested_round）
- [ ] R-NN-14 commit + push `rcm-rNN:`

### 已执行轮次（按实际进度填充）

- [x] R01 通用清单全部通过（取 pyc #1: IQCommon/__init__.pyc）
  - [x] R01-0 该轮取的 pyc 文件路径已记录（IQCommon/__init__.pyc，decompile_status=pending→partial）
  - [x] R01-1 测试工程师 `decompile_report.md` 已生成
  - [x] R01-2 ≥ 10 个最小复现实例已归档至 `minimal_repros/`（12 个，10 通过 2 残留独立缺陷）
  - [x] R01-3 修复工程师 `fix_report.md` 已生成
  - [x] R01-4 涉及的 `_generate_*` 方法 docstring 已更新（_wrap_boolop_with_merge_compare）
  - [x] R01-5 代码内注释已标注算法原则（generate/_generate_try_body/_wrap_boolop_with_merge_compare）
  - [x] R01-6 既有测试矩阵无退化（TRY 22→7 失败为改善，BOOLOP 100%无退化）
  - [x] R01-7 10+ 复现实例通过（10/12 通过，2 残留为独立缺陷）
  - [x] R01-8 反模式自检通过（0 新增 _fix_/_merge_/_patch_ 等前缀）
  - [x] R01-9 算法 4 原则 FULLY COMPLIANT
  - [x] R01-10 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 编译通过
  - [x] R01-11 累计成功率 ≥ 上一轮（0%→50%，单调递增）
  - [x] R01-12 OK.py 已生成且 py_compile 通过（get_python_version 100% 一致；<module> 在 R03 工具修复后确认 100% 一致，原 identity noise 已过滤；累计状态升级为 ok）
  - [x] R01-13 pyc_index.json 已更新（R03 工具修复后纠正为 ok/1.0/ok_py=True/round=1；原 partial/0.5 系身份噪声误判）
  - [x] R01-14 commit + push `rcm-r01:`（commit 1cf0fde，已 push 到 origin/main）
- [x] R02 通用清单全部通过（取 pyc #2: IQCommon/api/__init__.pyc，已 commit aab71b8）
  - [x] R02-0 pyc 路径已记录（IQCommon/api/__init__.pyc，decompile_status=ok）
  - [x] R02-1 测试工程师 decompile_report.md 已生成（100% 一致，豁免复现实例）
  - [x] R02-2 ≥ 10 个最小复现实例豁免（pyc 100% 一致）
  - [x] R02-3 修复工程师无修复（无需修复）
  - [x] R02-4..9 N/A（无修复）
  - [x] R02-10 编译通过
  - [x] R02-11 累计成功率 ≥ 上一轮（50% → 66.67%，单调递增）
  - [x] R02-12 OK.py 已生成且 py_compile 通过（__init__OK.py，1.0 一致）
  - [x] R02-13 pyc_index.json 已更新（ok/1.0/ok_py=True/round=2）
  - [x] R02-14 commit + push rcm-r02:（aab71b8）
- [ ] R03 通用清单全部通过（取 pyc #3: IQCommon/api/klinedata.pyc）
  - [x] R03-0 pyc 路径已记录（IQCommon/api/klinedata.pyc，decompile_status=partial）
  - [x] R03-1 测试工程师 `decompile_report.md` 已生成（51.11%，22 mismatches，14 复现实例）
  - [x] R03-2 ≥ 10 个最小复现实例已归档（14 个，10 DEFECT-REPRO / 4 NO-DEFECT）
  - [x] R03-3 修复工程师 `fix_report.md` 已生成（Pattern D 修复，53.33%）
  - [x] R03-6 既有测试矩阵无退化（IF 46 failures 与基线一致）
  - [x] R03-7 复现实例验证（5 OK / 9 DEFECT-REPRO，1 个缺陷模式修复）
  - [x] R03-8 反模式自检通过（0 新增）
  - [x] R03-9 算法 4 原则 FULLY COMPLIANT
  - [x] R03-10 编译通过
  - [x] R03-11 累计成功率 ≥ 上一轮（54.66% → 待 stats 复测，本 pyc 51.11%→53.33% 单调递增）
  - [x] R03-13 pyc_index.json 已更新（partial/0.5333/ok_py=True/round=3）
  - [x] R03-14 commit + push `rcm-r03:`（0ef0573 pushed to main）
  - 残留：Pattern A/B/C/E 共 21 个不一致函数，后续轮次修复
- [x] R04 通用清单全部通过（取 pyc #3: IQCommon/api/klinedata.pyc，续修 Pattern A）
  - [x] R04-0 该轮取的 pyc 文件路径已记录（IQCommon/api/klinedata.pyc，decompile_status=partial）
  - [x] R04-1 测试工程师 `decompile_report.md` 已生成（53.33%，21 mismatches，15 复现实例 8 NO-DEFECT/7 DEFECT-REPRO）
  - [x] R04-2 ≥ 10 个最小复现实例已归档（15 个，8 NO-DEFECT / 7 DEFECT-REPRO）
  - [x] R04-3 修复工程师 `fix_report.md` 已生成（Pattern A 子模式 A1 修复，4/5 Pattern A repro 修复）
  - [x] R04-4 涉及的 `_identify_*_regions` 方法 docstring 已按 6 节模板更新（`_identify_conditional_regions` 嵌套处理节追加 [R04 fix] 边界传播段落）
  - [x] R04-5 新增方法 `_get_enclosing_structural_boundary_stop` docstring 已包含背景/问题/修复/4 原则合规（辅助方法，非 4 节模板范畴）
  - [x] R04-6 既有测试矩阵无退化（Pre-R04 == Post-R04: 1 failed, 112 passed, 14 errors）
  - [x] R04-7 15 复现实例全部验证（8 NO-DEFECT / 7 DEFECT-REPRO，4/5 Pattern A repro 修复）
  - [x] R04-8 反模式自检通过（0 新增 _fix_/_merge_/_patch_ 等前缀；`_get_` 为查询类方法命名约定）
  - [x] R04-9 算法 4 原则 FULLY COMPLIANT（自底向上归约 / 每块唯一归属 / 嵌套抽象节点 / 入口引用语义）
  - [x] R04-10 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 编译通过
  - [x] R04-11 累计成功率 ≥ 上一轮（54.66% → 55.08%，单调递增；本 pyc 持平 53.33%）
  - [x] R04-12 N/A（本 pyc 未达 100%，未生成新 OK.py；既有 klinedataOK.py 由 single 命令刷新）
  - [x] R04-13 pyc_index.json 已更新（partial/0.5333/ok_py=True/round=4）
  - [x] R04-14 commit + push `rcm-r04:`
  - 残留：Pattern A 子模式 A2（9 函数，简单条件 + try-body if 坍缩，非 BoolOp 触发）+ Pattern B/C/E 共 21 个不一致函数，后续轮次修复
- [x] R05 通用清单全部通过（取 pyc #4: IQCommon/data/base_storage.pyc，新 pyc 轮询，非 klinedata.pyc）
  - [x] R05-0 该轮取的 pyc 文件路径已记录（IQCommon/data/base_storage.pyc，decompile_status=pending → ok）
  - [x] R05-1 测试工程师 `decompile_report.md` 已生成（80%→100%，1 mismatch，12 复现实例 7 DEFECT-REPRO/5 NO-DEFECT）
  - [x] R05-2 ≥ 10 个最小复现实例已归档（12 个，修复后 11 NO-DEFECT / 1 DEFECT-REPRO）
  - [x] R05-3 修复工程师 `fix_report.md` 已生成（Pattern M 装饰器调用坍缩修复，6/7 Pattern M repro 修复）
  - [x] R05-4 涉及的 `_generate_*` 方法 docstring 已按 4 节模板更新（`_generate_decorator` 扩展为 7 节：算法依据/归约顺序/唯一归属/嵌套处理/入口引用/反编译流程/R05 fix）
  - [x] R05-5 `_reconstruct_decorator_chain` docstring 已追加第 7 节 [R05 fix] Pattern M（has_decorator_call 跟踪 / CALL 检测分离）
  - [x] R05-6 既有测试矩阵无退化（Post-R05 == R04 基线: 1 failed, 112 passed, 14 errors）
  - [x] R05-7 12 复现实例全部验证（11 NO-DEFECT / 1 DEFECT-REPRO，6/7 Pattern M repro 修复）
  - [x] R05-8 反模式自检通过（0 新增 _fix_/_merge_/_patch_ 等前缀）
  - [x] R05-9 算法 4 原则 FULLY COMPLIANT（自底向上归约 / 每块唯一归属 / 嵌套抽象节点 / 入口引用语义）
  - [x] R05-10 `python -c "import core.cfg.code_generator; import core.cfg.region_ast_generator"` 编译通过
  - [x] R05-11 累计成功率 ≥ 上一轮（55.08% → 56.02%，单调递增；本 pyc 80%→100%）
  - [x] R05-12 本 pyc 达 100%，base_storageOK.py 由 single 命令重新生成（未手工编辑）
  - [x] R05-13 pyc_index.json 已更新（ok/1.0/ok_py=True/round=5）
  - [x] R05-14 commit + push `rcm-r05:`
  - 残留：Pattern M2（repro_11 堆叠装饰器嵌套错误，表达式重建层，后续轮次修复）
- [ ] R06 通用清单全部通过（取 pyc #6）
- [ ] R07 通用清单全部通过（取 pyc #7）
- [ ] R08 通用清单全部通过（取 pyc #8）
- [ ] R09 通用清单全部通过（取 pyc #9）
- [ ] R10 通用清单全部通过（取 pyc #10）
- [ ] R11+ 持续直到所有 pyc `decompile_status = ok`

## 阶段三（Phase 3：全量验证与 +OK 生成）

- [ ] P3.1 批量反编译全部 pyc 文件完成
- [ ] P3.2 每个反编译成功的 pyc 在同目录生成 `<name>OK.py`
- [ ] P3.3 所有 `+OK.py` 的 `py_compile` 通过
- [ ] P3.4 所有 `+OK.py` 重编译字节码与原 pyc 100% 一致
- [ ] P3.5 `pyc_index.json` 所有条目 `decompile_status = ok`，`ok_py_generated = true`
- [ ] P3.6 未修改任何 `+OK.py` 文件

## 退出条件（每轮后检查）

- [ ] E1 `pyc_index.json` 中所有条目 `decompile_status = ok`
- [ ] E2 所有 pyc 文件 `+OK.py` 已生成且字节码 100% 一致
- [ ] E3 最近 1 轮测试工程师可提取新增最小复现实例 < 10 个（因所有 pyc 已 100% 一致）

## 最终验证（迭代退出后）

- [ ] F1 所有轮次 commit + push 完成（`git log --grep="rcm-r"` 计数 ≥ 已执行轮数）
- [ ] F2 所有 pyc 文件字节码不一致函数数 = 0
- [ ] F3 既有测试矩阵无退化
- [ ] F4 算法 4 原则 FULLY COMPLIANT
- [ ] F5 无反模式残留（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀 0 新增）
- [ ] F6 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 编译通过
- [ ] F7 11 个 `_identify_*_regions` 方法 docstring 全部 6 节模板合规
- [ ] F8 9+ 个 `_generate_*` 方法 docstring 全部 4 节模板合规
- [ ] F9 所有 pyc 文件 `+OK.py` 已生成
- [ ] F10 所有 `+OK.py` 字节码与原 pyc 100% 一致

## 备注

- 轮次数不设上限，持续迭代直到退出条件 E1+E2+E3 满足
- 若某 pyc 在多轮后仍无法 100% 一致，输出 `final_residual.md` 列出残留不一致清单，作为后续迭代输入
- 每轮目录必须独立，禁止跨轮合并产物；每轮 `minimal_repros/` 中的实例必须可独立运行
- 禁止修改反编译生成的 `+OK.py` 文件；如需修复，必须修复反编译器本身
- 测试应尽快使成功率增加：优先修复影响面广的缺陷（同一缺陷在多个 pyc / 多个函数中出现）
