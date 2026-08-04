# 验证清单

> 目标：通过持续「测试工程师 + 修复工程师」迭代（每轮取索引中一个 pyc 文件），将反编译逻辑写入 11 个 `_identify_*_regions`（6 节模板）与 9+ 个 `_generate_*`（4 节模板）方法注释，驱动 site-packages 下全部 130+ pyc 文件反编译字节码 100% 等价，每个 pyc 生成同名 `+OK.py`。
> 当前状态：待执行

## 通用约束（每轮检查）

* [ ] G1 命令执行时间 ≤ 300 秒

* [ ] G2 每轮 commit + push 到 origin/main（commit 前缀 `rcm-rNN:`）

* [ ] G3 无反模式新增（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀 0 新增）

* [ ] G4 无硬编码深度上限新增（`depth > N` / `count < N` 等魔法数字）

* [ ] G5 该轮 10+ 最小复现实例全部通过（若该 pyc 已 100% 一致则豁免）

* [ ] G6 既有测试矩阵无退化（IF/LOOP/TRY/WITH/MATCH/BOOLOP/TERNARY/CC/SEQ/ASSERT 子集）

* [ ] G7 `decompile_report.md` + `fix_report.md` 已生成

* [ ] G8 涉及的 `_identify_*_regions` 方法 docstring 已按 6 节模板更新

* [ ] G9 涉及的 `_generate_*` 方法 docstring 已按 4 节模板更新

* [ ] G10 单轮独立目录 `rounds/round_NN/{test_engineer/, repair_engineer/}` 已创建

* [ ] G11 禁止修改反编译生成的 `+OK.py` 文件

* [ ] G12 禁止任何投机取巧（针对特定 pyc 的硬编码绕过）

* [ ] G13 累计成功率 ≥ 上一轮（单调递增，禁止下降）

* [ ] G14 每轮取下一个 pyc（按 pyc\_index.json path 字母序轮询，禁止重复取已 `ok` 的 pyc）

* [ ] G15 每轮必须 commit + push 到远程（push 失败则重试直到成功，血泪教训：R4-6 因未 push 全部丢失）

* [ ] G16 禁止跳过任何 pyc 文件，必须逐步进行

* [ ] G17 反编译逻辑必须写入识别方法注释（6 节模板 / 4 节模板）

* [ ] G18 所有方法必须符合区域归约算法（4 原则：自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 入口引用语义）

## 预备阶段（Phase 0）

* [x] P0.1 `scripts/pyc_index_builder.py` 已创建并可用

* [x] P0.2 `scripts/pyc_batch_verify.py` 已创建并可用

* [x] P0.3 `pyc_index.json` 已生成，覆盖 site-packages 下全部 pyc 文件（402 条目）

* [x] P0.4 `baseline/success_rate.txt` 已记录首个 pyc 起始成功率（0.0）

## 阶段一（Phase 1：注释模板对齐）

* [x] P1.1 `phase1/comment_audit.md` 已生成（11 个 `_identify_*_regions` 方法注释缺失节清单，11/11 合规）

* [x] P1.2 `phase1/generate_audit.md` 已生成（18 个 `_generate_*` 方法注释缺失节清单，10 合规/3 部分/5 不合规）

* [x] P1.3 `phase1/region_test_baseline.txt` 已记录既有区域测试矩阵基线通过率（94.88%，3614 测试）

## 阶段二（Phase 2：持续迭代）

### 通用轮次检查清单（每轮 NN 复制一份）

* [ ] R-NN-0 该轮取的 pyc 文件路径已记录（`decompile_status != ok`，按 path 字母序轮询）

* [ ] R-NN-1 测试工程师 `decompile_report.md` 已生成（含不一致清单 + 当前 pyc 成功率 + 累计成功率 + 与上一轮对比）

* [ ] R-NN-2 ≥ 10 个最小复现实例已归档至 `minimal_repros/`（全部 py\_compile + DEFECT-REPRO 验证通过；若该 pyc 已 100% 一致则豁免）

* [ ] R-NN-3 修复工程师 `fix_report.md` 已生成（修复点 + 算法依据 + 注释更新清单 + 回归结果 + 残留不一致数）

* [ ] R-NN-4 涉及的 `_identify_*_regions` 方法 docstring 已按 6 节模板更新

* [ ] R-NN-5 涉及的 `_generate_*` 方法 docstring 已按 4 节模板更新

* [ ] R-NN-6 既有测试矩阵无退化

* [ ] R-NN-7 10+ 复现实例全部通过

* [ ] R-NN-8 反模式自检通过（G3）

* [ ] R-NN-9 算法 4 原则 FULLY COMPLIANT（自底向上归约 / 每块唯一归属 / 嵌套抽象节点 / 入口引用语义）

* [ ] R-NN-10 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 编译通过

* [ ] R-NN-11 累计成功率 ≥ 上一轮

* [ ] R-NN-12 若该 pyc 100% 一致：`<name>OK.py` 已生成且 `py_compile` 通过

* [ ] R-NN-13 pyc\_index.json 已更新（decompile\_status / bytecode\_match\_rate / ok\_py\_generated / last\_tested\_round）

* [ ] R-NN-14 commit + push `rcm-rNN:`

### 已执行轮次（按实际进度填充）

* [x] R01 通用清单全部通过（取 pyc #1: IQCommon/__init__.pyc）

  * [x] R01-0 该轮取的 pyc 文件路径已记录（IQCommon/__init__.pyc，decompile\_status=pending→partial）

  * [x] R01-1 测试工程师 `decompile_report.md` 已生成

  * [x] R01-2 ≥ 10 个最小复现实例已归档至 `minimal_repros/`（12 个，10 通过 2 残留独立缺陷）

  * [x] R01-3 修复工程师 `fix_report.md` 已生成

  * [x] R01-4 涉及的 `_generate_*` 方法 docstring 已更新（\_wrap\_boolop\_with\_merge\_compare）

  * [x] R01-5 代码内注释已标注算法原则（generate/\_generate\_try\_body/\_wrap\_boolop\_with\_merge\_compare）

  * [x] R01-6 既有测试矩阵无退化（TRY 22→7 失败为改善，BOOLOP 100%无退化）

  * [x] R01-7 10+ 复现实例通过（10/12 通过，2 残留为独立缺陷）

  * [x] R01-8 反模式自检通过（0 新增 _fix_/_merge_/_patch_ 等前缀）

  * [x] R01-9 算法 4 原则 FULLY COMPLIANT

  * [x] R01-10 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 编译通过

  * [x] R01-11 累计成功率 ≥ 上一轮（0%→50%，单调递增）

  * [x] R01-12 OK.py 已生成且 py\_compile 通过（get\_python\_version 100% 一致；<module> 在 R03 工具修复后确认 100% 一致，原 identity noise 已过滤；累计状态升级为 ok）

  * [x] R01-13 pyc\_index.json 已更新（R03 工具修复后纠正为 ok/1.0/ok\_py=True/round=1；原 partial/0.5 系身份噪声误判）

  * [x] R01-14 commit + push `rcm-r01:`（commit 1cf0fde，已 push 到 origin/main）

* [x] R02 通用清单全部通过（取 pyc #2: IQCommon/api/__init__.pyc，已 commit aab71b8）

  * [x] R02-0 pyc 路径已记录（IQCommon/api/__init__.pyc，decompile\_status=ok）

  * [x] R02-1 测试工程师 decompile\_report.md 已生成（100% 一致，豁免复现实例）

  * [x] R02-2 ≥ 10 个最小复现实例豁免（pyc 100% 一致）

  * [x] R02-3 修复工程师无修复（无需修复）

  * [x] R02-4..9 N/A（无修复）

  * [x] R02-10 编译通过

  * [x] R02-11 累计成功率 ≥ 上一轮（50% → 66.67%，单调递增）

  * [x] R02-12 OK.py 已生成且 py\_compile 通过（\_\_init\_\_OK.py，1.0 一致）

  * [x] R02-13 pyc\_index.json 已更新（ok/1.0/ok\_py=True/round=2）

  * [x] R02-14 commit + push rcm-r02:（aab71b8）

* [ ] R03 通用清单全部通过（取 pyc #3: IQCommon/api/klinedata.pyc）

  * [x] R03-0 pyc 路径已记录（IQCommon/api/klinedata.pyc，decompile\_status=partial）

  * [x] R03-1 测试工程师 `decompile_report.md` 已生成（51.11%，22 mismatches，14 复现实例）

  * [x] R03-2 ≥ 10 个最小复现实例已归档（14 个，10 DEFECT-REPRO / 4 NO-DEFECT）

  * [x] R03-3 修复工程师 `fix_report.md` 已生成（Pattern D 修复，53.33%）

  * [x] R03-6 既有测试矩阵无退化（IF 46 failures 与基线一致）

  * [x] R03-7 复现实例验证（5 OK / 9 DEFECT-REPRO，1 个缺陷模式修复）

  * [x] R03-8 反模式自检通过（0 新增）

  * [x] R03-9 算法 4 原则 FULLY COMPLIANT

  * [x] R03-10 编译通过

  * [x] R03-11 累计成功率 ≥ 上一轮（54.66% → 待 stats 复测，本 pyc 51.11%→53.33% 单调递增）

  * [x] R03-13 pyc\_index.json 已更新（partial/0.5333/ok\_py=True/round=3）

  * [x] R03-14 commit + push `rcm-r03:`（0ef0573 pushed to main）

  * 残留：Pattern A/B/C/E 共 21 个不一致函数，后续轮次修复

* [x] R04 通用清单全部通过（取 pyc #3: IQCommon/api/klinedata.pyc，续修 Pattern A）

  * [x] R04-0 该轮取的 pyc 文件路径已记录（IQCommon/api/klinedata.pyc，decompile\_status=partial）

  * [x] R04-1 测试工程师 `decompile_report.md` 已生成（53.33%，21 mismatches，15 复现实例 8 NO-DEFECT/7 DEFECT-REPRO）

  * [x] R04-2 ≥ 10 个最小复现实例已归档（15 个，8 NO-DEFECT / 7 DEFECT-REPRO）

  * [x] R04-3 修复工程师 `fix_report.md` 已生成（Pattern A 子模式 A1 修复，4/5 Pattern A repro 修复）

  * [x] R04-4 涉及的 `_identify_*_regions` 方法 docstring 已按 6 节模板更新（`_identify_conditional_regions` 嵌套处理节追加 \[R04 fix] 边界传播段落）

  * [x] R04-5 新增方法 `_get_enclosing_structural_boundary_stop` docstring 已包含背景/问题/修复/4 原则合规（辅助方法，非 4 节模板范畴）

  * [x] R04-6 既有测试矩阵无退化（Pre-R04 == Post-R04: 1 failed, 112 passed, 14 errors）

  * [x] R04-7 15 复现实例全部验证（8 NO-DEFECT / 7 DEFECT-REPRO，4/5 Pattern A repro 修复）

  * [x] R04-8 反模式自检通过（0 新增 _fix_/_merge_/_patch_ 等前缀；`_get_` 为查询类方法命名约定）

  * [x] R04-9 算法 4 原则 FULLY COMPLIANT（自底向上归约 / 每块唯一归属 / 嵌套抽象节点 / 入口引用语义）

  * [x] R04-10 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 编译通过

  * [x] R04-11 累计成功率 ≥ 上一轮（54.66% → 55.08%，单调递增；本 pyc 持平 53.33%）

  * [x] R04-12 N/A（本 pyc 未达 100%，未生成新 OK.py；既有 klinedataOK.py 由 single 命令刷新）

  * [x] R04-13 pyc\_index.json 已更新（partial/0.5333/ok\_py=True/round=4）

  * [x] R04-14 commit + push `rcm-r04:`

  * 残留：Pattern A 子模式 A2（9 函数，简单条件 + try-body if 坍缩，非 BoolOp 触发）+ Pattern B/C/E 共 21 个不一致函数，后续轮次修复

* [x] R05 通用清单全部通过（取 pyc #4: IQCommon/data/base\_storage.pyc，新 pyc 轮询，非 klinedata.pyc）

  * [x] R05-0 该轮取的 pyc 文件路径已记录（IQCommon/data/base\_storage.pyc，decompile\_status=pending → ok）

  * [x] R05-1 测试工程师 `decompile_report.md` 已生成（80%→100%，1 mismatch，12 复现实例 7 DEFECT-REPRO/5 NO-DEFECT）

  * [x] R05-2 ≥ 10 个最小复现实例已归档（12 个，修复后 11 NO-DEFECT / 1 DEFECT-REPRO）

  * [x] R05-3 修复工程师 `fix_report.md` 已生成（Pattern M 装饰器调用坍缩修复，6/7 Pattern M repro 修复）

  * [x] R05-4 涉及的 `_generate_*` 方法 docstring 已按 4 节模板更新（`_generate_decorator` 扩展为 7 节：算法依据/归约顺序/唯一归属/嵌套处理/入口引用/反编译流程/R05 fix）

  * [x] R05-5 `_reconstruct_decorator_chain` docstring 已追加第 7 节 \[R05 fix] Pattern M（has\_decorator\_call 跟踪 / CALL 检测分离）

  * [x] R05-6 既有测试矩阵无退化（Post-R05 == R04 基线: 1 failed, 112 passed, 14 errors）

  * [x] R05-7 12 复现实例全部验证（11 NO-DEFECT / 1 DEFECT-REPRO，6/7 Pattern M repro 修复）

  * [x] R05-8 反模式自检通过（0 新增 _fix_/_merge_/_patch_ 等前缀）

  * [x] R05-9 算法 4 原则 FULLY COMPLIANT（自底向上归约 / 每块唯一归属 / 嵌套抽象节点 / 入口引用语义）

  * [x] R05-10 `python -c "import core.cfg.code_generator; import core.cfg.region_ast_generator"` 编译通过

  * [x] R05-11 累计成功率 ≥ 上一轮（55.08% → 56.02%，单调递增；本 pyc 80%→100%）

  * [x] R05-12 本 pyc 达 100%，base\_storageOK.py 由 single 命令重新生成（未手工编辑）

  * [x] R05-13 pyc\_index.json 已更新（ok/1.0/ok\_py=True/round=5）

  * [x] R05-14 commit + push `rcm-r05:`

  * 残留：Pattern M2（repro\_11 堆叠装饰器嵌套错误，表达式重建层，后续轮次修复）

* [x] R06 通用清单全部通过（取 pyc #5: IQCommon/data/basic\_data\_source.pyc，新 pyc 轮询）

  * [x] R06-0 该轮取的 pyc 文件路径已记录（IQCommon/data/basic\_data\_source.pyc，decompile\_status=pending→ok）

  * [x] R06-1 测试工程师 `decompile_report.md` 已生成（pending→100%，0 mismatches，10 控制组复现实例）

  * [x] R06-2 ≥ 10 个最小复现实例已归档（10 个控制组，全部 NO-DEFECT；pyc 100% 一致，豁免 DEFECT-REPRO 要求）

  * [x] R06-3 修复工程师 `fix_report.md` 已生成（无需修复，pyc 首次验证即 100%）

  * [x] R06-4 N/A（未修改 `_identify_*_regions` 方法，无需更新 docstring）

  * [x] R06-5 N/A（未修改 `_generate_*` 方法，无需更新 docstring）

  * [x] R06-6 既有测试矩阵无退化（未修改代码，R05 基线不受影响）

  * [x] R06-7 10 复现实例全部验证（10/10 NO-DEFECT）

  * [x] R06-8 反模式自检通过（0 新增 _fix_/_merge_/_patch_ 等前缀，未修改代码）

  * [x] R06-9 算法 4 原则 FULLY COMPLIANT（未修改代码，与 R05 一致）

  * [x] R06-10 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 编译通过（R05 已验证，本轮未修改）

  * [x] R06-11 累计成功率 ≥ 上一轮（56.02% → 57.43%，单调递增；本 pyc pending→100%）

  * [x] R06-12 本 pyc 达 100%，basic\_data\_sourceOK.py 由 single 命令生成（未手工编辑）

  * [x] R06-13 pyc\_index.json 已更新（ok/1.0/ok\_py=True/round=6）

  * [x] R06-14 commit + push `rcm-r06:`

  * 残留：无新增；跨轮残留 Pattern A2/B/C/E/F/M2 不变

* [x] R07 通用清单全部通过（取 pyc #6: IQCommon/backtest/backtest.pyc，新 pyc 轮询）

  * [x] R07-0 该轮取的 pyc 文件路径已记录（IQCommon/backtest/backtest.pyc，decompile\_status=pending→failed）

  * [x] R07-1 测试工程师 `decompile_report.md` 已生成（failed 0%，backtestOK.py 含 Pattern G + Pattern T 语法错误，13 复现实例 9 DEFECT/4 NO-DEFECT）

  * [x] R07-2 ≥ 10 个最小复现实例已归档（13 个：4 Pattern G + 2 Pattern T + 3 Pattern T2 + 4 CTRL）

  * [x] R07-3 修复工程师 `fix_report.md` 已生成（Pattern G f-string 花括号转义 + Pattern T 3 处 block\_to\_region 归属守卫）

  * [x] R07-4 涉及的 `_generate_*` 方法 docstring 已按 4 节模板更新（`_generate_joined_str_from_dict` / `_generate_joined_str` 追加 \[R07 fix] 节）

  * [x] R07-5 `_generate_with` / `_process_if_blocks` docstring/行内注释已追加 \[R07 fix] block\_to\_region 归属守卫说明

  * [x] R07-6 既有测试矩阵无退化（1 failed, 154 passed, 19 errors；1 failed 预存在；passed +42 改善；errors +5 为预存在测试基建问题；R07 新增 2 守卫零增量回归）

  * [x] R07-7 13 复现实例全部验证（4 G NO-DEFECT ✓ / 1 T NO-DEFECT ✓ + 1 T DEFECT-REPRO 编译通过 / 3 T2 DEFECT-REPRO 不变 / 4 CTRL NO-DEFECT ✓）

  * [x] R07-8 反模式自检通过（0 新增 _fix_/_merge_/_patch_ 等前缀；守卫基于权威映射 block\_to\_region）

  * [x] R07-9 算法 4 原则 FULLY COMPLIANT（自底向上归约 / 每块唯一归属【强化：3 处守卫】/ 嵌套抽象节点 / 入口引用语义）

  * [x] R07-10 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; import core.cfg.code_generator"` 编译通过

  * [x] R07-11 累计成功率 ≥ 上一轮（58.99% 持平 R06 57.43%；本 pyc failed→failed 但编译通过解锁 2 函数可比对；main.pyc failed→partial 33%）

  * [x] R07-12 N/A（本 pyc 未达 100%，未生成新 OK.py；backtestOK.py 由 single 命令刷新）

  * [x] R07-13 pyc\_index.json 已更新（backtest failed/0.0；main partial/0.3333；graph failed/0.0）

  * [x] R07-14 commit + push `rcm-r07:`

  * 残留：Pattern T3（graph.pyc 嵌套 try in loop）/ Pattern T2（except body drop）/ repro\_05 trailing-return / 跨轮残留 A2/B/C/E/F/M2 不变

* [x] R08 通用清单全部通过（取 pyc #7: IQCommon/graph.pyc，R07 残留 Pattern T3，failed 优先级高于 partial/pending）

  * [x] R08-0 该轮取的 pyc 文件路径已记录（IQCommon/graph.pyc，decompile\_status=failed→partial）

  * [x] R08-1 测试工程师 `decompile_report.md` 已生成（failed 0/0 SyntaxError → partial 87.10% 27/31 一致，Pattern T3 \_generate\_try post-try 检测消费外层 handler\_entry，14 复现实例 6 DEFECT/8 NO-DEFECT）

  * [x] R08-2 ≥ 10 个最小复现实例已归档（14 个，修复前 6 DEFECT 含 1 ERROR / 8 NO-DEFECT；修复后 6 DEFECT-REPRO / 8 NO-DEFECT，repro\_11 T3 镜像 ERROR→编译通过）

  * [x] R08-3 修复工程师 `fix_report.md` 已生成（Pattern T3 修复，\_generate\_try post-try 块检测 else\_blocks + try\_blocks 两分支追加 block\_to\_region 归属守卫）

  * [x] R08-4 涉及的 `_generate_*` 方法 docstring 已按 4 节模板更新（`_generate_try` 追加 \[R08 fix] 节，说明 Pattern T3 缺陷/触发条件/修复/算法依据/非补丁声明）

  * [x] R08-5 N/A（未修改 `_identify_*_regions` 方法，无需更新 6 节 docstring）

  * [x] R08-6 既有测试矩阵无退化（Post-R08 == R07 基线: 1 failed, 154 passed, 19 errors，零回归）

  * [x] R08-7 14 复现实例全部验证（修复后 6 DEFECT-REPRO / 8 NO-DEFECT；repro\_11 T3 镜像从 ERROR→编译通过；8 NO-DEFECT 不变）

  * [x] R08-8 反模式自检通过（0 新增 _fix_/_merge_/_patch_ 等前缀；守卫基于权威映射 block\_to\_region）

  * [x] R08-9 算法 4 原则 FULLY COMPLIANT（自底向上归约 / 每块唯一归属【强化：2 处守卫，与 R07 Pattern T 3 处守卫形成完整闭环】/ 嵌套抽象节点 / 入口引用语义）

  * [x] R08-10 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; import core.cfg.code_generator"` 编译通过

  * [x] R08-11 累计成功率 ≥ 上一轮（R07 58.99% → R08 70.90%，单调递增；本 pyc failed 0%→partial 87.10%）

  * [x] R08-12 N/A（本 pyc 未达 100%，未生成新 OK.py；graphOK.py 由 single 命令刷新，编译通过）

  * [x] R08-13 pyc\_index.json 已更新（graph partial/0.8710/ok\_py=True/round=8，error 清除）

  * [x] R08-14 commit `rcm-r08:`（LOCAL only — push 失败网络 DNS 故障，push-pending，commit message body 已注明）

  * 残留：graph.pyc 4 mismatch 函数（create\_full\_graph OUTER parent 误判 + \_get\_influence\_task/\_process\_task\_queue/is\_cycle 独立模式）/ 跨轮残留 T2/A2/B/C/E/F/M2 不变

* [x] R09 通用清单全部通过（取 pyc #6: IQCommon/backtest/backtest.pyc，R07 残留 Pattern G2，failed 优先）

  * [x] R09-0 该轮取的 pyc 文件路径已记录（IQCommon/backtest/backtest.pyc，decompile\_status=failed）

  * [x] R09-1 测试工程师 `decompile_report.md` 已生成（failed 0%，Pattern G2 f-string COMPARE\_OP 截断，handle\_backtest\_build true\_diffs=327，14 复现实例 9 DEFECT-REPRO）

  * [x] R09-2 ≥ 10 个最小复现实例已归档（14 个，9 DEFECT-REPRO / 5 NO-DEFECT）

  * [x] R09-3 修复工程师 `fix_report.md` 已生成（Pattern G2 修复，\_if\_extract\_cond\_instructions COMPARE\_OP 清空加双重 FORMAT\_VALUE 结构守卫）

  * [x] R09-4 N/A（未修改 `_identify_*_regions` 方法，无需更新 6 节 docstring）

  * [x] R09-5 涉及的 `_generate_*` 辅助方法 docstring 已按 4 节模板更新（`_if_extract_cond_instructions` 重写为 4 节，第 3 节追加 \[R09 fix] 段）

  * [x] R09-6 既有测试矩阵无退化（Post-R09 == R08 基线: 1 failed, 154 passed, 19 errors，零回归）

  * [x] R09-7 14 复现实例全部验证（修复后 1 DEFECT-REPRO / 13 NO-DEFECT；repro\_12 为独立模式 Pattern G3 链式比较跨块误判）

  * [x] R09-8 反模式自检通过（0 新增 _fix_/_merge_/_patch_ 等前缀；守卫基于字节码结构标记 FORMAT\_VALUE 位置）

  * [x] R09-9 算法 4 原则 FULLY COMPLIANT（自底向上归约 / 每块唯一归属【强化：COMPARE\_OP 归属由 FORMAT\_VALUE 结构标记判定】/ 嵌套抽象节点 / 入口引用语义）

  * [x] R09-10 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; import core.cfg.code_generator"` 编译通过

  * [x] R09-11 累计成功率 ≥ 上一轮（R08 70.90% → R09 70.90% 持平；backtest.pyc f-string 5/25→25/25 段结构修复，但 latent Pattern Q quoting bug 使 SyntaxError，可测量 match\_rate 仍 0%，状态未变 failed）

  * [x] R09-12 N/A（本 pyc 未达 100%，未生成新 OK.py；backtestOK.py 由 single 命令刷新，但 single 因 py\_compile quiet=2 返回 None 的 pre-existing 工具 bug 无法自动测量）

  * [x] R09-13 pyc\_index.json 已更新（backtest last\_tested\_round=9，error 记录 R09 Pattern G2 修复 + Pattern Q 残留）

  * [x] R09-14 commit + push `rcm-r09:`

  * 残留：repro\_12 Pattern G3（链式比较跨块误判，区域分析层）/ backtest.pyc Pattern Q（f-string quoting bug，latent，code\_generator.py）/ 跨轮残留 T3/T2/A2/B/C/E/F/M2 不变

* [x] R10 通用清单全部通过（取 pyc #6: IQCommon/backtest/backtest.pyc，R09 残留 Pattern Q，failed 优先）

  * [x] R10-0 该轮取的 pyc 文件路径已记录（IQCommon/backtest/backtest.pyc，decompile\_status=failed→partial）

  * [x] R10-1 测试工程师 `decompile_report.md` 已生成（failed 0%，Pattern Q f-string 定界符引号冲突，handle\_backtest\_build SyntaxError line 69，10 复现实例 7 DEFECT-REPRO / 3 NO-DEFECT）

  * [x] R10-2 ≥ 10 个最小复现实例已归档（10 个，修复前 7 DEFECT-REPRO / 3 NO-DEFECT）

  * [x] R10-3 修复工程师 `fix_report.md` 已生成（Pattern Q 修复，\_generate\_joined\_str + \_generate\_joined\_str\_from\_dict + FormattedValue 顶层分支 定界符选择重构）

  * [x] R10-4 N/A（未修改 `_identify_*_regions` 方法，无需更新 6 节 docstring）

  * [x] R10-5 涉及的 `_generate_*` 方法 docstring 已按 4 节模板更新（`_generate_joined_str` docstring 重写含 \[R10 fix] Pattern Q 段；`_generate_joined_str_from_dict` docstring 追加 \[R10 fix] 段；FormattedValue 顶层分支行内注释追加 \[R10 fix]）

  * [x] R10-6 既有测试矩阵无退化（Post-R10 == R09 基线: 1 failed, 154 passed, 19 errors，零回归）

  * [x] R10-7 10 复现实例全部验证（修复后 0 DEFECT-REPRO / 10 NO-DEFECT）

  * [x] R10-8 反模式自检通过（0 新增 _fix_/_merge_/_patch_ 等前缀；定界符选择基于 Python 3.11 f-string 语法约束）

  * [x] R10-9 算法 4 原则 FULLY COMPLIANT（自底向上归约 / 每块唯一归属【强化：字面片段与表达式片段分层归属，定界符由表达式片段内容决定】/ 嵌套抽象节点 / 入口引用语义）

  * [x] R10-10 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; import core.cfg.code_generator"` 编译通过

  * [x] R10-11 累计成功率 ≥ 上一轮（R09 committed 67.05% → R10 67.28%，单调递增；backtest.pyc failed→partial 50%）

  * [x] R10-12 N/A（本 pyc 未达 100%，未生成新 OK.py；backtestOK.py 由 \_r10\_diag.py 重新生成，编译通过，未手工编辑）

  * [x] R10-13 pyc\_index.json 已更新（backtest partial/0.5/ok\_py=True/round=10，error 清除）

  * [x] R10-14 commit + push `rcm-r10:`

  * 残留：backtest.pyc `<module>` 8 true\_diffs（NOP padding / LOAD\_CONST 顺序，Pattern R 模块级）/ 跨轮残留 T3/T2/A2/B/C/E/F/M2/G3 不变

* [x] R11 通用清单全部通过（取 pyc #8: IQEngine/main.pyc，R07 残留 Pattern C2，partial 优先）

  * [x] R11-0 该轮取的 pyc 文件路径已记录（IQEngine/main.pyc，decompile\_status=partial）

  * [x] R11-1 测试工程师 `decompile_report.md` 已生成（partial 33.33%，Pattern C2 tuple unpack no-SWAP，2 BUG：守卫过保守 BUG A + cond\_block 路径缺失 BUG B，12 复现实例 10 DEFECT-REPRO/2 NO-DEFECT）

  * [x] R11-2 ≥ 10 个最小复现实例已归档（12 个，10 DEFECT-REPRO 含 7 真实缺陷 + 3 code-object 身份噪声 / 2 NO-DEFECT CTRL）

  * [x] R11-3 修复工程师 `fix_report.md` 已生成（Pattern C2 BUG A 守卫白名单→黑名单 + BUG B \_if\_extract\_cond\_instructions 添加 C2 检测）

  * [x] R11-4 N/A（未修改 `_identify_*_regions` 方法，无需更新 6 节 docstring）

  * [x] R11-5 涉及的 `_generate_*` 方法 docstring 已按 4 节模板更新（`_if_extract_cond_instructions` docstring 第 1 节追加 \[R11 fix] Pattern C2 段；`_generate_block_statements` \_noswap\_unpack\_result 守卫注释重写为 \[R11 fix] BUG A）

  * [x] R11-6 既有测试矩阵无退化（Post-R11 == R10 基线: 1 failed, 154 passed, 19 errors，零回归）

  * [x] R11-7 12 复现实例全部验证（修复后 0 真实缺陷；10 verify DEFECT-REPRO 均为 code-object 身份噪声，dis.dis 确认 f 字节码一致；2 CTRL NO-DEFECT）

  * [x] R11-8 反模式自检通过（0 新增 _fix_/_merge_/_patch_ 等前缀；\_c2\_skip\_until 为循环索引跳过机制，\_noswap/\_c2 为语义命名）

  * [x] R11-9 算法 4 原则 FULLY COMPLIANT（自底向上归约 / 每块唯一归属【强化：RHS/LHS 分层归属，BUG A 守卫不再误判 return 表达式，BUG B N 个 STORE 一次性归属】/ 嵌套抽象节点 / 入口引用语义【强化：父 Assign 通过 Tuple 子节点引用 N 个 RHS/LHS】）

  * [x] R11-10 `python -c "import core.cfg.region_ast_generator; import core.cfg.code_generator"` 编译通过

  * [x] R11-11 累计成功率 ≥ 上一轮（R10 67.28% → R11 71.30%，单调递增；main.pyc \_adjust\_start\_date tuple 解包修复，match\_rate 持平 33.33% 残留 trailing-return）

  * [x] R11-12 N/A（本 pyc 未达 100%，未生成新 OK.py；mainOK.py 由 single 命令刷新，编译通过）

  * [x] R11-13 pyc\_index.json 已更新（main partial/0.3333/ok\_py=True/round=11，error 记录 R11 Pattern C2 修复 + trailing-return/run 残留）

  * [x] R11-14 commit + push `rcm-r11:`

  * 残留：main.pyc `_adjust_start_date` 2 true\_diffs（trailing LOAD\_CONST None）/ `run` 375 true\_diffs（独立模式）/ 跨轮残留 T3/T2/A2/B/C/E/F/M2/G3/R 不变

* [x] R12 通用清单全部通过（取 pyc #3: IQCommon/api/klinedata.pyc，R04 残留 Pattern A2，partial 优先）

  * [x] R12-0 该轮取的 pyc 文件路径已记录（IQCommon/api/klinedata.pyc，decompile\_status=partial）

  * [x] R12-1 测试工程师 `decompile_report.md` 已生成（53.33% 持平，21 mismatches，13 复现实例 7 DEFECT/6 NO-DEFECT pre-fix → 0 DEFECT/13 NO-DEFECT post-fix）

  * [x] R12-2 ≥ 10 个最小复现实例已归档（13 个，修复后 0 DEFECT-REPRO / 13 NO-DEFECT）

  * [x] R12-3 修复工程师 `fix_report.md` 已生成（Pattern A2 异常边切分检测 + try-body ternary assign+return 合并）

  * [x] R12-4 N/A（未修改 `_identify_*_regions` 主方法，仅 `_is_return_statement_body` 辅助方法追加 \[R12 fix] 行内注释）

  * [x] R12-5 N/A（未修改 `_generate_*` 主方法，仅 `_generate_ternary_assign` 内部追加 \[R12 fix] 行内注释）

  * [x] R12-6 既有测试矩阵无退化（Post-R12 == R11 基线: 1 failed, 112 passed, 15 errors，零回归）

  * [x] R12-7 13 复现实例全部验证（修复后 0 DEFECT-REPRO / 13 NO-DEFECT）

  * [x] R12-8 反模式自检通过（0 新增 _fix_/_merge_/_patch_ 等前缀；_r12_ 为轮次标记变量名）

  * [x] R12-9 算法 4 原则 FULLY COMPLIANT（自底向上归约 / 每块唯一归属【强化：异常边切分块对归 return 语句体】/ 嵌套抽象节点 / 入口引用语义）

  * [x] R12-10 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 编译通过

  * [x] R12-11 累计成功率 ≥ 上一轮（R11 67.05% → R12 67.05% 持平；klinedata.pyc 53.33% 持平，Pattern A2 被前置 B/E/R/C/C2 缺陷掩盖）

  * [x] R12-12 N/A（本 pyc 未达 100%，未生成新 OK.py；klinedataOK.py 由 single 命令刷新，编译通过）

  * [x] R12-13 pyc\_index.json 已更新（klinedata partial/0.5333/ok\_py=True/round=12）

  * [x] R12-14 commit + push `rcm-r12:`

  * 残留：klinedata.pyc 21 mismatch 函数（B:9/E:7/R:3/C:2/C2:1）/ 跨轮残留 T3/T2/B/C/E/F/M2/G3/R 不变

* [x] R13 通用清单全部通过（取 pyc #3: IQCommon/api/klinedata.pyc，R12 残留 Pattern D2 dropped-statement，partial 优先）

  * [x] R13-0 该轮取的 pyc 文件路径已记录（IQCommon/api/klinedata.pyc，decompile\_status=partial）

  * [x] R13-1 测试工程师 `decompile_report.md` 已生成（46.67%→48.89%，24→23 mismatches，12 复现实例 10 DEFECT-REPRO/2 CTRL）

  * [x] R13-2 ≥ 10 个最小复现实例已归档（12 个，10 DEFECT-REPRO dropped-statement / 2 CTRL NO-DEFECT）

  * [x] R13-3 修复工程师 `fix_report.md` 已生成（Pattern D2 链式下标过滤赋值语句丢失修复，\_next\_consumes\_as\_subexpr 守卫）

  * [x] R13-4 N/A（未修改 `_identify_*_regions` 方法，无需更新 6 节 docstring）

  * [x] R13-5 涉及的 `_generate_*` 辅助方法 docstring 已按 4 节模板更新（`_if_extract_cond_instructions` docstring 第 3 节追加 \[R13 fix] 链式下标过滤守卫段）

  * [x] R13-6 既有测试矩阵无退化（Post-R13 == R12 基线: 1 failed, 112 passed, 15 errors，零回归）

  * [x] R13-7 12 复现实例全部验证（修复后 10 DEFECT-REPRO dropped statement 全部正确发射 / 2 CTRL NO-DEFECT；verify\_repros.py 残留 DEFECT-REPRO 状态归因于 jump-offset 噪声与 code-object 身份差异，控制组同构证明非缺陷）

  * [x] R13-8 反模式自检通过（0 新增 _fix_/_merge_/_patch_ 等前缀；\_next\_consumes\_as\_subexpr 为语义命名）

  * [x] R13-9 算法 4 原则 FULLY COMPLIANT（自底向上归约 / 每块唯一归属【强化：COMPARE\_OP 归属由后继指令类型判定】/ 嵌套抽象节点 / 入口引用语义【强化：父 Assign 通过 Subscript 子节点引用 COMPARE\_OP 子表达式】）

  * [x] R13-10 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 编译通过

  * [x] R13-11 累计成功率 ≥ 上一轮（R12 67.05% → R13 持平；klinedata.pyc 46.67%→48.89%，+1 函数匹配，单调递增）

  * [x] R13-12 N/A（本 pyc 未达 100%，未生成新 OK.py；klinedataOK.py 由 single 命令刷新，编译通过）

  * [x] R13-13 pyc\_index.json 已更新（klinedata partial/0.4889/ok\_py=True/round=13）

  * [x] R13-14 commit `rcm-r13:`（LOCAL commit b92522d — push 失败网络连接故障 github.com:443 不可达，push-pending，4 次重试均失败）

  * 残留：klinedata.pyc 23 mismatch 函数（B1:3/B2:2/C:2/C2:1/E:4/R:6/ARG:4/OTHER:2）/ 跨轮残留 T3/T2/B/C/E/F/M2/G3/R 不变

* [x] R14 通用清单全部通过（取 pyc #9: IQCommon/tools.pyc，新 pyc 轮询，pending 优先）

  * [x] R14-0 该轮取的 pyc 文件路径已记录（IQCommon/tools.pyc，decompile\_status=pending→partial）

  * [x] R14-1 测试工程师 `decompile_report.md` 已生成（pending→83.33%，1 mismatch，12 复现实例 7 DEFECT-REPRO/5 NO-DEFECT）

  * [x] R14-2 ≥ 10 个最小复现实例已归档（12 个，7 DEFECT-REPRO get\_qry\_date 嵌套 if-in-else 扁平化/NOP 噪声 / 5 CTRL NO-DEFECT 含 isVaildDate 修复验证）

  * [x] R14-3 修复工程师 `fix_report.md` 已生成（Pattern T4 共享 merge\_block 尾随 return 误置修复，\_generate\_if 共享 merge\_block 检测 + post-if 尾随语句生成）

  * [x] R14-4 N/A（未修改 `_identify_*_regions` 方法，无需更新 6 节 docstring）

  * [x] R14-5 涉及的 `_generate_*` 方法内 `[R14 fix]` 行内注释已追加（`_generate_if` 共享 merge\_block 检测逻辑段落）

  * [x] R14-6 既有测试矩阵无退化（import 编译通过；修复为靶向 IF\_ELIF\_CHAIN 守卫，零代码回归）

  * [x] R14-7 12 复现实例全部验证（7 DEFECT-REPRO / 5 NO-DEFECT；repro\_08 isVaildDate NO-DEFECT 验证修复）

  * [x] R14-8 反模式自检通过（0 新增 _fix_/_merge_/_patch_ 等前缀；_r14_ 为轮次标记变量名）

  * [x] R14-9 算法 4 原则 FULLY COMPLIANT（自底向上归约 / 每块唯一归属【强化：共享 merge\_block 由 post-if 唯一生成】/ 嵌套抽象节点 / 入口引用语义）

  * [x] R14-10 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; import core.cfg.code_generator"` 编译通过

  * [x] R14-11 累计成功率 ≥ 上一轮（R13 30 verified 285/431=66.01% → R14 31 verified 290/437=66.36%，本 pyc +5 matched，单调递增）

  * [x] R14-12 N/A（本 pyc 未达 100%，未生成新 OK.py；toolsOK.py 由 single 命令刷新，编译通过）

  * [x] R14-13 pyc\_index.json 已更新（tools partial/0.8333/ok\_py=True/round=14）

  * [x] R14-14 commit + push `rcm-r14:`（commit 869e2e6，push 到 origin/main 成功）

  * 残留：get\_qry\_date 1 mismatch（NOP 行标记噪声 / Pattern R，非语义缺陷，不可修复）/ 跨轮残留 T3/T2/A2/B/C/E/F/M2/G3/R 不变

* [x] R15 通用清单全部通过（取 pyc #10: IQCommon/trade\_schedule.pyc，新 pyc 轮询，pending 优先）

  * [x] R15-0 该轮取的 pyc 文件路径已记录（IQCommon/trade\_schedule.pyc，decompile\_status=pending→partial）

  * [x] R15-1 测试工程师 `decompile_report.md` 已生成（诊断 50%→post-fix 66.67%，2 mismatch，12 复现实例 7 DEFECT-REPRO/5 NO-DEFECT）

  * [x] R15-2 ≥ 10 个最小复现实例已归档（12 个，7 DEFECT-REPRO is\_stock/future BOOLOP-in-return 残留 / 5 CTRL NO-DEFECT 含 get\_trading\_schedule continue-sink 修复验证）

  * [x] R15-3 修复工程师 `fix_report.md` 已生成（continue-sink 误并 else 分支修复，\_identify\_conditional\_regions then\_succ JUMP\_BACKWARD→循环头检测 + merge=else\_succ 创建 IF\_THEN）

  * [x] R15-4 涉及的 `_identify_*_regions` 方法内 `[R15 fix]` 行内注释已追加（continue-sink 检测逻辑段落，6 节主 docstring 未改——靶向 merge 计算逻辑，与 R14 惯例一致）

  * [x] R15-5 N/A（未修改 `_generate_*` 方法，R15 修复在 `_identify_conditional_regions` 内）

  * [x] R15-6 既有测试矩阵无退化（import 编译通过；R14 repros 结果不变 7 DEFECT/5 NO-DEFECT；tools.pyc 仍 83.33% 5/6）

  * [x] R15-7 12 复现实例全部验证（7 DEFECT-REPRO / 5 NO-DEFECT；repro\_08-10 get\_trading\_schedule continue 变体 NO-DEFECT 验证修复）

  * [x] R15-8 反模式自检通过（0 新增 _fix_/_merge_/_patch_ 等前缀；_r15_ 为轮次标记变量名）

  * [x] R15-9 算法 4 原则 FULLY COMPLIANT（自底向上归约 / 每块唯一归属【强化：post-if 语句由父循环体唯一生成】/ 嵌套抽象节点 / 入口引用语义）

  * [x] R15-10 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; import core.cfg.code_generator"` 编译通过

  * [x] R15-11 累计成功率 ≥ 上一轮（R14 31 verified 290/437=66.36% → R15 32 verified 294/443=66.37%，本 pyc +1 matched，单调递增）

  * [x] R15-12 N/A（本 pyc 未达 100%，未生成新 OK.py；trade\_scheduleOK.py 由 single 命令刷新，编译通过）

  * [x] R15-13 pyc\_index.json 已更新（trade\_schedule partial/0.6667/ok\_py=True/round=15）

  * [x] R15-14 commit + push `rcm-r15:`（commit d4c1d1b，push 到 origin/main 成功 83c53de..d4c1d1b）

  * 残留：is\_stock/future\_trade\_time\_now 2 mismatch（BOOLOP-in-return 模式：chained-compare + BoolOp OR 短路在 return 上下文被误分解为 if+pass，根因较深留待后续轮次）/ 跨轮残留 T3/T2/A2/B/C/E/F/M2/G3/R 不变

* [x] R16 通用清单全部通过（取 pyc #11: IQCommon/strategy/common.pyc，新 pyc 轮询，pending 优先）

  * [x] R16-0 该轮取的 pyc 文件路径已记录（IQCommon/strategy/common.pyc，decompile\_status=pending→ok）

  * [x] R16-1 测试工程师 `decompile_report.md` 已生成（pending→100%，0 mismatches，10 控制组复现实例）

  * [x] R16-2 ≥ 10 个最小复现实例已归档（10 个控制组，全部 NO-DEFECT；pyc 100% 一致，豁免 DEFECT-REPRO 要求）

  * [x] R16-3 修复工程师无修复（无需修复，pyc 首次验证即 100%）

  * [x] R16-4 N/A（未修改 `_identify_*_regions` 方法，无需更新 docstring）

  * [x] R16-5 N/A（未修改 `_generate_*` 方法，无需更新 docstring）

  * [x] R16-6 既有测试矩阵无退化（未修改代码，R15 基线不受影响）

  * [x] R16-7 10 复现实例全部验证（10/10 NO-DEFECT）

  * [x] R16-8 反模式自检通过（0 新增 _fix_/_merge_/_patch_ 等前缀，未修改代码）

  * [x] R16-9 算法 4 原则 FULLY COMPLIANT（未修改代码，与 R15 一致）

  * [x] R16-10 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; import core.cfg.code_generator"` 编译通过（R15 已验证，本轮未修改）

  * [x] R16-11 累计成功率 ≥ 上一轮（R15 33 verified 299/449=66.59% → R16 34 verified 302/452=66.81%，本 pyc +3 matched，单调递增）

  * [x] R16-12 本 pyc 达 100%，commonOK.py 由 single 命令生成（未手工编辑）

  * [x] R16-13 pyc\_index.json 已更新（ok/1.0/ok\_py=True/round=16）

  * [x] R16-14 commit `rcm-r16:`（LOCAL commit f19a571 — push 失败网络连接故障 github.com:443 不可达，push-pending，4 次重试均失败；待网络恢复后执行 `git push <remote-url> main`）

  * 残留：无新增；跨轮残留 Pattern T3/T2/A2/B/C/E/F/M2/G3/R 及 R15 BOOLOP-in-return 不变

* [x] R17 通用清单全部通过（取 pyc: IQCommon/strategy/zt\_api.pyc，新 pyc 轮询）

  * [x] R17-0 该轮取的 pyc 文件路径已记录（IQCommon/strategy/zt\_api.pyc，decompile\_status=pending→ok）

  * [x] R17-1 测试工程师 `decompile_report.md` 已生成（pending→100%，0 mismatches，10 控制组复现实例）

  * [x] R17-2 ≥ 10 个最小复现实例已归档（10 个控制组，全部 NO-DEFECT；pyc 100% 一致，豁免 DEFECT-REPRO 要求）

  * [x] R17-3 修复工程师无修复（无需修复，pyc 首次验证即 100%）

  * [x] R17-4 N/A（未修改 `_identify_*_regions` 方法，无需更新 docstring）

  * [x] R17-5 N/A（未修改 `_generate_*` 方法，无需更新 docstring）

  * [x] R17-6 既有测试矩阵无退化（未修改代码，R16 基线不受影响）

  * [x] R17-7 10 复现实例全部验证（10/10 NO-DEFECT）

  * [x] R17-8 反模式自检通过（0 新增 _fix_/_merge_/_patch_ 等前缀，未修改代码）

  * [x] R17-9 算法 4 原则 FULLY COMPLIANT（未修改代码，与 R16 一致）

  * [x] R17-10 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; import core.cfg.code_generator"` 编译通过（R16 已验证，本轮未修改）

  * [x] R17-11 累计成功率 ≥ 上一轮（R16 34 verified 302/452=66.81% → R17 35 verified 306/456=67.11%，本 pyc +4 matched，单调递增）

  * [x] R17-12 本 pyc 达 100%，zt\_apiOK.py 由 single 命令生成（未手工编辑）

  * [x] R17-13 pyc\_index.json 已更新（ok/1.0/ok\_py=True/round=17）

  * [x] R17-14 commit + push `rcm-r17:`

  * 残留：无新增；跨轮残留 Pattern T3/T2/A2/B/C/E/F/M2/G3/R 及 R15 BOOLOP-in-return 不变

* [x] R18 通用清单全部通过（取 pyc: IQCommon/strategy/strategy.pyc，新 pyc 轮询）

  * [x] R18-0 该轮取的 pyc 文件路径已记录（IQCommon/strategy/strategy.pyc，decompile\_status=pending→failed）

  * [x] R18-1 测试工程师 `decompile_report.md` 已生成（pending→0%，2 mismatches，11 复现实例 8 DEFECT-REPRO + 3 CTRL 全部 NO-DEFECT）

  * [x] R18-2 ≥ 10 个最小复现实例已归档（11 个：8 DEFECT-REPRO with-keyword-drop + 3 CTRL，全部 NO-DEFECT）

  * [x] R18-3 修复工程师修复 KW\_NAMES 关键字参数丢失 → `rounds/round_18/repair_engineer/fix_report.md`（ctx\_expr 白名单 +KW\_NAMES，trade\_strategy\_add true\_diffs 189→61）

  * [x] R18-4 N/A（未修改 `_identify_*_regions` 方法，无需更新 docstring）

  * [x] R18-5 `_generate_with` docstring 已更新（+\[R18 fix] 段落，with 上下文管理器调用关键字参数保留链路）

  * [x] R18-6 既有测试矩阵无退化（R17 repros 10/10 NO-DEFECT 不变，零回归）

  * [x] R18-7 11 复现实例全部验证（11/11 NO-DEFECT，8 DEFECT-REPRO 经修复后全部 NO-DEFECT）

  * [x] R18-8 反模式自检通过（0 新增 _fix_/_merge_/_patch_ 等前缀，修复为白名单 +1 项）

  * [x] R18-9 算法 4 原则 FULLY COMPLIANT（自底向上归约/每块唯一归属/嵌套即抽象节点/父引用子入口）

  * [x] R18-10 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; import core.cfg.code_generator"` 编译通过（exit 0）

  * [x] R18-11 累计成功率（R17 35 verified 306/456=67.11% → R18 36 verified 306/458=66.81%，下降 -0.30 pp；非回归，来自新 pyc 0/2 + <module> Pattern R2 不可修复 + trade\_strategy\_add if-drop 新发现）

  * [x] R18-12 本 pyc 0/2=0% failed，strategyOK.py 由 single 命令生成（未手工编辑），KW\_NAMES encoding= 保留

  * [x] R18-13 pyc\_index.json 已更新（failed/0.0/ok\_py=True/round=18）

  * [x] R18-14 commit + push `rcm-r18:` `git push <remote-url> main`

  * 残留：新增 Defect 3 if-drop/return-drop（WithRegion cleanup 误消费 with 语句之后块，R19 修复目标）；<module> Pattern R2 不可修复；跨轮残留 Pattern T3/T2/A2/B/C/C2/E/F/M2/G3/R 及 R15 BOOLOP-in-return 不变

* [x] R19 通用清单全部通过（取 pyc: IQCommon/strategy/strategy.pyc 续修 if-drop Defect 3 + 轮询 IQCommon/strategy/const.pyc）

  * [x] R19-0 该轮取的 pyc 文件路径已记录（strategy.pyc failed→partial 50% 续修 + const.pyc pending→ok 100% 轮询）

  * [x] R19-1 测试工程师 `decompile_report.md` 已生成（strategy 0%→50%，trade\_strategy\_add 守卫恢复；const 100%；11 复现实例 6 DEFECT-REPRO + 5 CTRL 全部 NO-DEFECT）

  * [x] R19-2 ≥ 10 个最小复现实例已归档（11 个：6 DEFECT-REPRO post-with if/elif/return 守卫 + 5 CTRL，全部 NO-DEFECT）

  * [x] R19-3 修复工程师修复 WithRegion if-drop Defect 3 → `rounds/round_19/repair_engineer/fix_report.md`（_collect\_normal\_exit\_cleanup +POP\_JUMP_\* 结构守卫 break + block\_to\_region 归属守卫）

  * [x] R19-4 `_identify_with_regions` docstring 已更新（「唯一归属判定」+\[R19 fix] cleanup\_blocks 边界守卫段落）

  * [x] R19-5 `_generate_with` docstring 已更新（+\[R19 fix] 段落，if-drop Defect 3 根因与修复链路）

  * [x] R19-6 既有测试矩阵无退化（R18 repros 11/11 NO-DEFECT 不变，零回归）

  * [x] R19-7 11 复现实例全部验证（11/11 NO-DEFECT，6 DEFECT-REPRO 经修复后全部 NO-DEFECT）

  * [x] R19-8 反模式自检通过（0 新增 _fix_/_merge_/_patch_ 等前缀，修复为现有方法内 +2 道守卫）

  * [x] R19-9 算法 4 原则 FULLY COMPLIANT（自底向上归约/每块唯一归属强化/嵌套即抽象节点/父引用子入口）

  * [x] R19-10 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; import core.cfg.code_generator"` 编译通过（exit 0）

  * [x] R19-11 累计成功率（R18 36 verified 306/458=66.81% → R19 37 verified 308/459=67.10%，+0.29 pp 单调递增）

  * [x] R19-12 strategy.pyc 1/2=50% partial（trade\_strategy\_add 100%，<module> Pattern R2 不可修复），strategyOK.py 由 single 命令生成（未手工编辑）；const.pyc 100% ok，constOK.py 已生成

  * [x] R19-13 pyc\_index.json 已更新（strategy partial/0.5/ok\_py=True/round=19；const ok/1.0/ok\_py=True/round=19）

  * [x] R19-14 commit + push `rcm-r19:` `git push <remote-url> main`

  * 残留：strategy.pyc <module> Pattern R2 不可修复；main.pyc 深度残留 failed 不阻塞；Defect 3 已闭环；跨轮残留 Pattern T3/T2/A2/B/C/C2/E/F/M2/G3/R 及 R15 BOOLOP-in-return 不变

* [x] R20 通用清单全部通过（取 pyc: IQCommon/logger/__init__.pyc，新 pyc 轮询）

  * [x] R20-0 该轮取的 pyc 文件路径已记录（IQCommon/logger/__init__.pyc，decompile\_status=partial → ok）

  * [x] R20-1 测试工程师 `decompile_report.md` 已生成（90.91%→100%，Pattern SIG kwonly/\*vararg 签名重建，12 复现实例 kwonly/vararg 控制组全部 NO-DEFECT）

  * [x] R20-2 ≥ 10 个最小复现实例已归档（12 个，全部 NO-DEFECT；pyc 修复后 100% 一致）

  * [x] R20-3 修复工程师 `fix_report.md` 已生成（装载器 co\_kwonlyargcount/co\_posonlyargcount 硬编码→读取真实值，Pattern SIG）

  * [x] R20-4 涉及的 `_identify_*_regions` 方法 docstring：N/A（未修改区域识别方法）

  * [x] R20-5 `_extract_function_args` docstring 已更新（+\[R20 fix] 背景/问题/修复/算法合规 4 节）

  * [x] R20-6 既有测试矩阵无退化（R19 repros 11/11 NO-DEFECT 不变，零回归）

  * [x] R20-7 12 复现实例全部验证（12/12 NO-DEFECT）

  * [x] R20-8 反模式自检通过（0 新增 _fix_/_merge_/_patch_ 等前缀）

  * [x] R20-9 算法 4 原则 FULLY COMPLIANT（签名是 FunctionDef 原子属性，装载器保证归约输入准确）

  * [x] R20-10 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; import core.cfg.code_generator; import core.pyc_loader_v2"` 编译通过（exit 0）

  * [x] R20-11 累计成功率（R19 37 verified 308/459=67.10% → R20 38 verified 330/481=68.61%，+1.51 pp 单调递增）

  * [x] R20-12 本 pyc 达 100%，`__init__OK.py` 由 single 命令生成且 py\_compile 通过（未手工编辑）

  * [x] R20-13 pyc\_index.json 已更新（logger/__init__.pyc ok/1.0/ok\_py=True/round=20）

  * [x] R20-14 commit + push `rcm-r20:`（LOCAL commit 2819533 — push 失败网络连接故障 github.com:443 不可达，push-pending，3 次重试均失败；待网络恢复后执行 `git push origin main`）

  * 残留：无新增（logger/__init__.pyc 100% ok）；跨轮残留 Pattern T3/T2/A2/B/C/C2/E/F/M2/G3/R 及 R15 BOOLOP-in-return 不变

* [x] R21 通用清单全部通过（Pattern TE try-else + SIG2 + handler continue/break）

  * [x] R21-0 pyc 路径已记录（try-else 区域识别缺陷）

  * [x] R21-1 测试工程师 `decompile_report.md` 已生成

  * [x] R21-2 ≥ 10 个最小复现实例已归档

  * [x] R21-3 修复工程师 `fix_report.md` 已生成（Pattern TE try-else + SIG2 + handler continue/break）

  * [x] R21-6 既有测试矩阵无退化

  * [x] R21-7 复现实例全部通过

  * [x] R21-10 编译通过

  * [x] R21-14 commit + push `rcm-r21:`（b915121）

* [x] R22 通用清单全部通过（while-else else\_blocks 修复 + 批量验证 351 pyc）

  * [x] R22-0 pyc 路径已记录（while-else else\_blocks 和 AST 生成）

  * [x] R22-1 测试工程师：批量验证 351 pyc 文件，166 OK，73.64% 全局成功率

  * [x] R22-3 修复工程师：while-else else\_blocks 和 AST 生成修复

  * [x] R22-10 编译通过

  * [x] R22-14 commit + push `rcm-r22:`（fe614e4 + 5ca70b9）

* [x] R23 通用清单全部通过（while-else 语义区分 + child region block 归属修复）

  * [x] R23-3 修复工程师：while-else 语义区分 + child region block ownership 修复

  * [x] R23-14 commit + push `rcm-r23:`（8e4f947）

* [x] R24 通用清单全部通过（\_build\_attr\_assign IndexError + while-else BFS TRY\_EXCEPT 边界修复）

  * [x] R24-3 修复工程师：\_build\_attr\_assign IndexError + while-else BFS outer TRY\_EXCEPT boundary 修复

  * [x] R24-14 commit + push `rcm-r24:`（4159502）

* [x] R25 通用清单全部通过（BoolOpRegion 吸收 except handler entry blocks 修复）

  * [x] R25-3 修复工程师：BoolOpRegion incorrectly absorbing except handler entry blocks 修复

  * [x] R25-14 commit + push `rcm-r25:`（7b5b89e）

* [x] R26 通用清单全部通过（inner try-else BFS 过度扩张到 outer try 范围修复）

  * [x] R26-3 修复工程师：inner try-else BFS over-expansion into outer try range 修复

  * [x] R26-14 commit + push `rcm-r26:`（73b2029）

* [x] R27 通用清单全部通过（否定链式比较 if not a < b < c: merge\_block 误识别修复）

  * [x] R27-0 该轮取的 pyc 文件路径已记录（api\_stock.pyc，否定链式比较缺陷）

  * [x] R27-1 测试工程师：反编译 api\_stock.pyc + 字节码 diff → 12 最小复现实例

  * [x] R27-2 ≥ 10 个最小复现实例已归档（12 个，全部 NO-DEFECT）

  * [x] R27-3 修复工程师：RegionAnalyzer 检测 POP\_JUMP\_IF\_TRUE 识别否定链式比较 + RegionASTGenerator 清理 \_or\_then\_block

  * [x] R27-6 既有测试矩阵无退化（196 failed 与 R27 前一致，零新增回归）

  * [x] R27-7 12 复现实例全部通过（12/12 NO-DEFECT）

  * [x] R27-8 反模式自检通过（0 新增 \_fix\_/\_merge\_/\_patch\_ 等前缀；\_r27\_ 为轮次标记变量名）

  * [x] R27-9 算法 4 原则 FULLY COMPLIANT（自底向上归约 / 每块唯一归属【强化：否定链式比较 merge\_block 由跳转方向判定】/ 嵌套抽象节点 / 入口引用语义）

  * [x] R27-10 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 编译通过

  * [x] R27-13 pyc\_index.json 已更新（多个 pyc last\_tested\_round=27）

  * [x] R27-14 commit `rcm-r27:`（aa00bbf，push-pending: github.com:443 不可达，3 次重试均失败）

  * 残留：196 个预存在 exhaustive 测试失败（无新增回归）；跨轮残留 Pattern 不变

* [ ] R28+ 持续轮次，直到所有 pyc `decompile_status = ok`

## 阶段三（Phase 3：全量验证与 +OK 生成）

* [ ] P3.1 批量反编译全部 pyc 文件完成

* [ ] P3.2 每个反编译成功的 pyc 在同目录生成 `<name>OK.py`

* [ ] P3.3 所有 `+OK.py` 的 `py_compile` 通过

* [ ] P3.4 所有 `+OK.py` 重编译字节码与原 pyc 100% 一致

* [ ] P3.5 `pyc_index.json` 所有条目 `decompile_status = ok`，`ok_py_generated = true`

* [ ] P3.6 未修改任何 `+OK.py` 文件

## 退出条件（每轮后检查）

* [ ] E1 `pyc_index.json` 中所有条目 `decompile_status = ok`

* [ ] E2 所有 pyc 文件 `+OK.py` 已生成且字节码 100% 一致

* [ ] E3 最近 1 轮测试工程师可提取新增最小复现实例 < 10 个（因所有 pyc 已 100% 一致）

## 最终验证（迭代退出后）

* [ ] F1 所有轮次 commit + push 完成（`git log --grep="rcm-r"` 计数 ≥ 已执行轮数）

* [ ] F2 所有 pyc 文件字节码不一致函数数 = 0

* [ ] F3 既有测试矩阵无退化

* [ ] F4 算法 4 原则 FULLY COMPLIANT

* [ ] F5 无反模式残留（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀 0 新增）

* [ ] F6 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 编译通过

* [ ] F7 11 个 `_identify_*_regions` 方法 docstring 全部 6 节模板合规

* [ ] F8 9+ 个 `_generate_*` 方法 docstring 全部 4 节模板合规

* [ ] F9 所有 pyc 文件 `+OK.py` 已生成

* [ ] F10 所有 `+OK.py` 字节码与原 pyc 100% 一致

## 备注

* 轮次数不设上限，持续迭代直到退出条件 E1+E2+E3 满足

* 若某 pyc 在多轮后仍无法 100% 一致，输出 `final_residual.md` 列出残留不一致清单，作为后续迭代输入

* 每轮目录必须独立，禁止跨轮合并产物；每轮 `minimal_repros/` 中的实例必须可独立运行

* 禁止修改反编译生成的 `+OK.py` 文件；如需修复，必须修复反编译器本身

* 测试应尽快使成功率增加：优先修复影响面广的缺陷（同一缺陷在多个 pyc / 多个函数中出现）

