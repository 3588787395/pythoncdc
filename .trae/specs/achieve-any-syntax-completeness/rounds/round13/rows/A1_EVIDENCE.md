# A1 agv2 集合守卫解遮蔽 — 证据记录（结局一：分支被到达且产品一致）

修复（单行 diff，HEAD 52128723，行数零漂移，BOM/CRLF 完好）：
`core/cfg/ast_generator_v2.py` L23464 五成员集合纳入 `'CHECK_EG_MATCH'`,
`'PREP_RERAISE_STAR'`（行尾标记 `[R215-STAGE2-A1]`）。

## 被测对象

JS-EXCEPTSTAR 家族 96 条（J 空间 `round9/judgment_space.json`，1556 条中
96 条 id 前缀 JS-EXCEPTSTAR，全部共享 pyc `test_repros/round4/c4_03_except_star.pyc`，
pyc sha16 见 a1_before.json / a1_after.json）。pyc opcode 普查：
CHECK_EG_MATCH×14、PREP_RERAISE_STAR×12、RERAISE×28、PUSH_EXC_INFO×14、
POP_EXCEPT×39、WITH_EXCEPT_START×1、CHECK_EXC_MATCH×0（773 指令，12 个嵌套 code object）。

## 分支可达性（sys.settrace 行级 + opname 级，legacy_v2 管线）

| 行 | 内容 | before | after（次数） | after（opname 对账） |
|---|---|---|---|---|
| 23464 | 守卫集合求值 | 279 | 279 | 新入集成员：CHECK_EG_MATCH×2、PREP_RERAISE_STAR×6；原成员 RERAISE×4、PUSH_EXC_INFO×1、POP_EXCEPT×3 |
| 23484 | elif RERAISE 测试 | 4 | 12 | RERAISE×4 + CHECK_EG_MATCH×2 + PREP_RERAISE_STAR×6 |
| 23489 | elif CHECK_EXC_MATCH 测试 | 0 | 8 | CHECK_EG_MATCH×2 + PREP_RERAISE_STAR×6 |
| 23494 | **elif CHECK_EG_MATCH（遮蔽分支）** | **0** | **8** | **CHECK_EG_MATCH×2（命中 2 次）** + PREP_RERAISE_STAR×6（下落） |
| 23499 | **elif PREP_RERAISE_STAR（遮蔽分支）** | **0** | **6** | **PREP_RERAISE_STAR×6（命中 6 次）** |

- 修复前两 elif 行执行 0 次（结构性遮蔽实证）；修复后 CHECK_EG_MATCH 分支体执行 2 次、
  PREP_RERAISE_STAR 分支体执行 6 次（elif 链逐行计数与守卫行入集 opcode 完全对账）。
- pyc 级 opcode 计数（14/12）中未到达守卫的部分（12/6）被更早的 except* 结构处理
  消费，未进入 `_process_instruction_sequence` 指令循环——与阶段一 probe
  「3113 次进入、区域路径先行消费」定性一致。
- region 管线：五目标行全部 0 次执行（before/after 相同）——修复不影响 region
  路径（_process_instruction_sequence 仅 legacy_v2 调用，与阶段一 probe 读数一致）。

## 产品逐字对比（before vs after）

| 产品 | before | after | 结论 |
|---|---|---|---|
| legacy_v2 文本（CFGCodeGenerator.generate 输出） | C40A243F574405A4 / 1890 字符 | C40A243F574405A4 / 1890 字符 | **逐字节一致**（a1_before_legacy.py == a1_after_legacy.py） |
| region 文本 | 7F318B44E905C9AE / 1883 字符 | 7F318B44E905C9AE / 1883 字符 | **逐字节一致** |
| legacy ast_dict 序列化 | 1B4639F136AB85CB | B6ECD7E355DB7B5D | 唯一差异＝code object repr 的运行时内存地址（0x…，跨进程非确定）；掩码 0x[0-9A-F]{8,16} 后**全同** ACDB971EC231B91A |

JS-EXCEPTSTAR 96 条共享同一 pyc，模块级产品逐字节一致 ⇒ 96/96 条目
legacy_v2 产品不变；region 产品不变 ⇒ 该家族 J 读数无扰动。

## 结局判定（父代理裁决树）

**结局一（分支被到达且产品一致）→ 保留修复，两遮蔽分支转可证路径：**
- RULE-a310f7ea600b（PREP_RERAISE_STAR@ast_generator_v2.py:23499@HEAD）：
  锚点谓词 `opname == 'PREP_RERAISE_STAR'` 修复后被求值 6 次且 6 次为真
  → 正见证就位，转可证路径（G4 复测确认见 A3）。
- 相邻 CHECK_EG_MATCH@23494（非追踪规则，阶段一已注明）：同步解遮蔽，命中 2 次。
- 无产品变化 ⇒ 无 EQUAL 翻转记录义务、无回滚义务。

## 工件

- a1_harness.py / a1_opnames.py（harness）
- a1_before.json / a1_after.json / a1_opnames_after.json（读数）
- a1_before_legacy.py / a1_after_legacy.py / a1_before_region.py /
  a1_after_region.py / a1_before_ast.json / a1_after_ast.json（产品与中间态）
