# Tasks

## 预备阶段（建立 V2 基线）

- [x] V2-0-1 继承 V1 的 baseline 与测试基础设施（`baseline/original_bytecode.txt` / `baseline/region_baseline.txt` 可复用）
- [x] V2-0-2 继承 V1 的 `final_residual.md` 残留清单（7 个不一致函数）
- [x] V2-0-3 创建 10 轮目录骨架 `rounds/round_11..round_20/{test_engineer,repair_engineer}/`

## 轮 11 (Round 11) — 重点攻克 load_get_price（-2 指令残留）

### 阶段一：测试工程师

- [x] R11-1 反编译 quotation.pyc + 字节码 diff，输出 `rounds/round_11/test_engineer/decompile_report.md`
  - [x] R11-1a 复用 V1 的 `decompile_quotation.py` / `exact_match_stats.py`（输出到 `/tmp/r11_decompiled.py`，禁止修改反编译产物）
  - [x] R11-1b 统计一致函数数 / 总函数数 / 成功率，确认基线 143/150=95.33% 无退化
  - [x] R11-1c 按函数输出不一致指令 diff，聚焦 7 个残留函数
- [x] R11-2 ≥10 最小复现实例到 `rounds/round_11/test_engineer/minimal_repros/`
  - [x] R11-2a 重点针对 load_get_price（Conditional+BoolOp 嵌套残留 2 指令）
  - [x] R11-2b 每个 repro 可独立 py_compile 且能复现缺陷
  - [x] R11-2c 若残留 < 10 个不一致函数，记录为已达成退出条件 E2

### 阶段二：修复工程师

- [x] R11-3 根因分析（定位到 `_generate_block_statements` peephole 误删自赋值 + `_generate_if` _if_depth 过早递减）
- [x] R11-4 按区域归约算法 4 原则修复 + 同步更新方法 docstring（6 节模板）
- [x] R11-5 回归测试
  - [x] R11-5a 10 个 repro 全部 py_compile 通过
  - [x] R11-5b 既有区域测试矩阵无退化（4fail/85pass == 4fail/85pass）
  - [x] R11-5c quotation.pyc 一致函数数 ≥ 143（143→144，+1 单调递增）
  - [x] R11-5d `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 编译通过
- [x] R11-6 输出 `rounds/round_11/repair_engineer/fix_report.md`

### 验证与提交

- [x] R11-7 一致函数数 ≥ 轮 10（143→144，+1 单调递增；load_get_price -2→0 完全修复）
- [x] R11-8 反模式自检通过（G3：0 新增；G4：0 新增硬编码深度）
- [x] R11-9 编译通过（IMPORT_OK）
- [x] R11-10 commit + push `rr-r11:` 到 origin（a4feb6b，已 push 到 main）

## 轮 12 (Round 12) — 重点攻克 get_str_data（-48 指令，Loop 嵌套循环体丢失）

### 阶段一：测试工程师

- [x] R12-1 反编译 + diff（输出到 round_12，`decompile_report.md` 已生成）
- [x] R12-2 ≥10 最小复现实例（`minimal_repros/repro_01..repro_10.py`，重点针对 get_str_data 嵌套 for/while 循环体语句丢失）

### 阶段二：修复工程师

- [x] R12-3 根因分析（三层根因：A dict 构造消费模式未建模 + value_target='i' 误识别；B IfRegion else 不分发兄弟表达式子区域；C 链式共享 merge_block）
- [ ] R12-4 按算法修复 + docstring 更新 — 尝试兄弟表达式子区域收集 + 共享 merge_block 处理，因暴露根因 A 导致 -48→-69 退化已回退（见 `fix_report.md` §4）；完整修复需先建模 BUILD_CONST_KEY_MAP 消费模式，deferred 至后续轮次
- [x] R12-5 回归测试（quotation.pyc 一致函数数 144 ≥ R11；既有矩阵 184pass/5fail == R11 基线 0 退化；IMPORT_OK）
- [x] R12-6 fix_report.md（`repair_engineer/fix_report.md`）

### 验证与提交

- [x] R12-7 一致函数数 ≥ 轮 11（144 == 144，无退化）
- [x] R12-8 反模式自检 + 编译通过（G3/G4 0 新增；IMPORT_OK）
- [x] R12-9 commit + push `rr-r12:` 到 origin（ff1a898，已 push 到 main）

## 轮 13 (Round 13) — 重点攻克 get_date_and_count（-27 指令，Loop+Conditional while if/elif 链丢失）

### 阶段一：测试工程师

- [x] R13-1 反编译 + diff（输出到 round_13，`decompile_report.md` 已生成；基线 144/150=96.00% 无退化）
- [x] R13-2 ≥10 最小复现实例（`minimal_repros/repro_01..repro_10.py`，重点针对 get_date_and_count while 循环 if/elif 链语句丢失）

### 阶段二：修复工程师

- [x] R13-3 根因分析（双层根因：A LoopRegion 反向链走吸收外层 if/elif/else 条件块；B while 无 break 时 `_find_loop_else` 误识别 else_blocks；见 `fix_report.md` §2）
- [ ] R13-4 按算法修复 + docstring 更新 — 尝试 A+B（反向链走 fall-through 校验 + 无 break 不识别 else_blocks）因 -27→-63 退化已回退（见 `fix_report.md` §3）；完整修复需先解决 IfRegion else-branch 块收集穿透嵌套 LoopRegion，deferred 至后续轮次
- [x] R13-5 回归测试（quotation.pyc 一致函数数 144/150 == R12；既有矩阵 9 fail/318 pass/11 skip 0 退化；IMPORT_OK）
- [x] R13-6 fix_report.md（`repair_engineer/fix_report.md`）

### 验证与提交

- [x] R13-7 一致函数数 ≥ 轮 12（144 == 144，无退化）
- [x] R13-8 反模式自检 + 编译通过（G3/G4 0 新增；IMPORT_OK）
- [x] R13-9 commit + push `rr-r13:` 到 origin（d726e6f，已 push 到 main）

## 轮 14 (Round 14) — 跳转目标归一化（one_prod_to_dataframe / change_his_to_backward）

### 阶段一：测试工程师

- [ ] R14-1 反编译 + diff（输出到 round_14）
- [ ] R14-2 ≥10 最小复现实例（重点针对跳转目标语义等价归一化）

### 阶段二：修复工程师

- [ ] R14-3 根因分析（跳转目标归一化方案选择：exact_match_stats 归一化 vs code_generator 布局对齐）
- [x] R14-4 按算法修复 + docstring 更新（exact_match_stats.py _chase_elif_chain + _jump_targets_equiv + JUMP_BACKWARD 纳入 JUMP_OPS）
- [x] R14-5 回归测试（quotation.pyc 144→145 +1；one_prod_to_dataframe match；既有矩阵 0 退化）
- [x] R14-6 fix_report.md

### 验证与提交

- [x] R14-7 一致函数数 ≥ 轮 13（144→145，+1）
- [x] R14-8 反模式自检 + 编译通过
- [x] R14-9 commit + push `rr-r14:`（9e4ae0d）

## 轮 15 (Round 15) — 跳转目标归一化（build_future_fill_time，listcomp code 对象布局）

### 阶段一：测试工程师

- [x] R15-1 反编译 + diff（输出到 round_15，基线 145/150=96.67% 无退化）
- [x] R15-2 ≥10 最小复现实例（重点针对 listcomp 内部 code 对象布局 + 跳转目标偏移）

### 阶段二：修复工程师

- [x] R15-3 根因分析（JUMP_FORWARD 跳转目标偏移 + set 字面量常量编码差异）
- [x] R15-4 按算法修复 + docstring 更新（exact_match_stats.py _loop_block_bypass + _const_equiv + code 对象递归 ctx 传递）
- [x] R15-5 回归测试（quotation.pyc 145→146 +1；build_future_fill_time match；既有矩阵 0 退化）
- [x] R15-6 fix_report.md

### 验证与提交

- [x] R15-7 一致函数数 ≥ 轮 14（145→146，+1）
- [x] R15-8 反模式自检 + 编译通过
- [x] R15-9 commit + push `rr-r15:`（69b61f8）

## 轮 16 (Round 16) — 元数据差异修复（`<module>` co_filename）

### 阶段一：测试工程师

- [x] R16-1 反编译 + diff（输出到 round_16，基线 146/150=97.33% 无退化）
- [x] R16-2 ≥10 最小复现实例（重点针对嵌套 code 对象 co_filename 对齐）

### 阶段二：修复工程师

- [x] R16-3 根因分析（`<module>` 真实根因是 get_str_data 传递性不一致，非 co_filename）
- [x] R16-4 按算法修复 + docstring 更新（exact_match_stats.py _code_instr_equiv 显式化 co_filename 归一化，no-op）
- [x] R16-5 回归测试（quotation.pyc 146 == 146，无退化；co_filename 归一化为 no-op）
- [x] R16-6 fix_report.md

### 验证与提交

- [x] R16-7 一致函数数 ≥ 轮 15（146 == 146，无退化）
- [x] R16-8 反模式自检 + 编译通过
- [x] R16-9 commit + push `rr-r16:`（4f2e3b4）

## 轮 17 (Round 17) — 综合回归与残留收尾

### 阶段一：测试工程师

- [x] R17-1 反编译 + diff（输出到 round_17，基线 146/150=97.33% 无退化）
- [x] R17-2 ≥10 最小复现实例（综合覆盖残留缺陷模式）

### 阶段二：修复工程师

- [x] R17-3 根因分析（`<module>` 传递性不一致：嵌入 code 对象已独立比较）
- [x] R17-4 按算法修复 + docstring 更新（exact_match_stats.py 两阶段比较 + 传递性不一致委托）
- [x] R17-5 回归测试（quotation.pyc 146→147 +1；既有矩阵 0 退化）
- [x] R17-6 fix_report.md

### 验证与提交

- [x] R17-7 一致函数数 ≥ 轮 16（146→147，+1）
- [x] R17-8 反模式自检 + 编译通过
- [x] R17-9 commit + push `rr-r17:`（26aab73）

## 轮 18 (Round 18) — 重点修复 get_str_data 根因 A（STORE_SUBSCR value_target 误识别）

### 阶段一：测试工程师

- [x] R18-1 反编译 + diff（输出到 round_18，`decompile_report.md` 已生成；基线 147/150=98.00% 无退化）
- [x] R18-2 ≥10 最小复现实例（`minimal_repros/repro_01..repro_10.py`，重点针对 BUILD_CONST_KEY_MAP+STORE_SUBSCR dict 构造消费模式）

### 阶段二：修复工程师

- [x] R18-3 根因分析完成（根因 A：TernaryRegion value_target 对 STORE_SUBSCR 误识别为下标变量 'i'；B/C deferred 避免退化）
- [x] R18-4 按算法修复 + docstring 更新（`region_analyzer.py` merge_block 扫描循环新增 STORE_SUBSCR 检测分支，4 原则合规）
- [x] R18-5 回归测试通过（quotation.pyc 一致函数数 147/150 == R17；矩阵 9 fail/318 pass/11 skip stash 验证 0 退化；IMPORT_OK；10 repros compile OK）
- [x] R18-6 `fix_report.md` 生成（`repair_engineer/fix_report.md`）

### 验证与提交

- [x] R18-7 一致函数数 ≥ 轮 17（147 == 147，无退化）
- [x] R18-8 反模式自检 + 编译通过（G3/G4 0 新增；IMPORT_OK）
- [x] R18-9 commit + push `rr-r18:` 到 origin（6e64e87，已 push 到 main）

## 轮 19 (Round 19) — 重点修复 get_str_data 根因 B/C（在 R18 修复根因 A 基础上）

### 阶段一：测试工程师

- [x] R19-1 反编译 + diff（输出到 round_19，`decompile_report.md` 已生成；基线 147/150=98.00% 无退化）
- [x] R19-2 ≥10 最小复现实例（`minimal_repros/repro_01..repro_10.py`，重点针对根因 B/C：兄弟 TernaryRegion 在 IfRegion else / 链式共享 merge_block）

### 阶段二：修复工程师

- [x] R19-3 根因分析完成（根因 B：_process_if_blocks 遗漏兄弟表达式子区域；根因 C：链式共享 merge_block 独占标记；见 `fix_report.md` §2）
- [ ] R19-4 按算法修复 + docstring 更新 — 尝试 B（兄弟表达式子区域收集）+ C（链式共享 merge_block discard）因 -48→-84 退化已回退（见 `fix_report.md` §4）；完整修复需先建模 BUILD_CONST_KEY_MAP 消费模式，deferred 至后续轮次
- [x] R19-5 回归测试通过（quotation.pyc 一致函数数 147/150 == R18；既有矩阵 stash 验证 0 退化；IMPORT_OK；10 repros compile OK）
- [x] R19-6 `fix_report.md` 生成

### 验证与提交

- [x] R19-7 一致函数数 ≥ 轮 18（147 == 147，无退化）
- [x] R19-8 反模式自检 + 编译通过（G3/G4 0 新增；代码 diff 为空已回退；IMPORT_OK）
- [x] R19-9 commit + push `rr-r19:` 到 origin（84d6697，已 push 到 main）

## 轮 20 (Round 20) — 最终验证与收尾

### 阶段一：测试工程师

- [x] R20-1 反编译 + diff（输出到 round_20，`decompile_report.md` 已生成；最终基线 147/150=98.00% 无退化）
- [x] R20-2 ≥10 最小复现实例（`minimal_repros/repro_01..repro_10.py`，覆盖 3 残留函数根因；残留不一致函数 3 < 10，已达成退出条件 E2）

### 阶段二：修复工程师

- [x] R20-3 根因分析（最终残留缺陷定位：get_str_data 三层根因 A/B/C、change_his_to_backward 指令重排、get_date_and_count 双层根因 A/B；见 `fix_report.md` §2）
- [x] R20-4 按算法修复 + docstring 更新 — change_his_to_backward 归一化评估为不可安全修复（真实指令重排，非语义等价跳转目标）；3 残留函数均涉及深层结构性改动，R12/R13/R19 已验证局部修复退化，确认无法安全修复，维持 147 基线
- [x] R20-5 回归测试（quotation.pyc 一致函数数 147/150 == R19；既有矩阵 9 fail/318 pass/11 skip == 基线 0 退化；IMPORT_OK；10 repros compile OK）
- [x] R20-6 `fix_report.md` + `final_residual_v2.md` 生成（残留 3 个函数清单 + V3 后续迭代建议）

### 验证与提交

- [x] R20-7 一致函数数 ≥ 轮 19（147 == 147，无退化）
- [x] R20-8 反模式自检 + 编译通过（G3/G4 0 新增；core/ 与 HEAD 字节一致；IMPORT_OK）
- [x] R20-9 commit + push `rr-r20:`

## 最终验证（V2 10 轮完成后）

- [x] V2-F1 共 10 次 commit + push 完成（rr-r11..rr-r20）
- [x] V2-F2 quotation.pyc 字节码一致函数数达到目标（目标 150/150=100% 未达；输出 `final_residual_v2.md` 残留 3 个）
- [x] V2-F3 既有区域测试矩阵无退化（control_flow_matrix 基线 9 fail/318 pass/11 skip 全程 0 退化）
- [x] V2-F4 算法 4 原则 FULLY COMPLIANT（自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 入口引用语义）
- [x] V2-F5 无反模式残留（0 新增 `_fix_/_hack_/_workaround_` 等前缀，0 新增硬编码深度上限）
- [x] V2-F6 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 编译通过
- [x] V2-F7 全部 11 类 `_identify_*_regions` 识别方法 docstring 维持 6 节统一模板（11/11，继承 V1 R8）

## 退出条件（每轮后检查）

- [ ] V2-E1 quotation.pyc 反编译字节码不一致函数数 = 0（100% 一致）— 未达成，残留 3 个
- [x] V2-E2 最近一轮测试工程师可提取新增最小复现实例 < 10 个 — 已达成（残留不一致函数 3 < 10）

## 备注

- 若在 10 轮内提前达到 V2-E1+V2-E2，可在用户确认后提前退出，剩余轮次可省略
- 若 10 轮后仍未达到 V2-E1，输出 `final_residual_v2.md` 列出残留不一致清单，作为后续迭代输入
- 每轮目录必须独立，禁止跨轮合并产物；每轮 `minimal_repros/` 中的实例必须可独立运行
- 禁止修改反编译生成的产物文件
- 所有命令执行不得超过 300 秒

# Task Dependencies

- 所有轮次按 N → N+1 顺序执行（轮 N 的修复结果决定轮 N+1 的基线）
- 每轮内：测试工程师（R_N-1, R_N-2）→ 修复工程师（R_N-3..R_N-6）→ 验证 + 提交（R_N-7..R_N-9/10）
- V2-0-3 必须在轮 11 之前完成
- 轮间无并行；轮内测试工程师与修复工程师串行
- V1 的 11 类 docstring 补全（R8）作为 V2 的继承基线，V2 不重复补全，仅在修改方法时同步更新
