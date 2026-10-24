# B142 族级修复探针与判据（Task 2.3 / 2.5）

规范：`achieve-any-syntax-completeness` Task 2（修复 B142 嵌套 finally/continue，族级）。

## 一、族级谓词与影响面（Task 2.3）

### 根因族

CPython 3.11 把 `finally` 体按**出口路径就地内联**为多份副本（正常出口 / 控制流出口 /
异常出口）。嵌套 `try/finally` 时，内层 try 的出口路径上先出现**内层副本**、再出现
**外层副本**，而异常表只覆盖部分跨度。本族缺陷 = 副本块（含其承载的控制流终结符：
continue 回边 / break 出口跳转 / return 值装载+RETURN）被错误归属：

1. 内层 region 越权吸收外层副本与异常路径体（Pattern-A 正常路径走查、cleanup 走查）；
2. 内层副本因异常表边界切分的 NOP 胶水块而漏登记（被吸收为体语句 → 重复发射）；
3. 外层副本被内层 try_blocks 收集（发射端按内层体语句重复发射）；
4. 副本块承载的 continue/break 终结符不物化（continue 整条消失，B181）；
5. 出口 if 被误判为字面量 match（`match r: case 0: pass`，continue 丢失）。

### 修复判据（全部为结构事实，无 B142/测试名/输入值专用分支）

| 判据 | 位置 | 内容 |
|---|---|---|
| 副本体签名 | `region_analyzer._finally_body_signature` | 各 finally handler 异常路径入口块 `PUSH_EXC_INFO..RERAISE` 之间的 `(opname, argval)` 序列 |
| 透明链副本搜索 | `_collect_finally_body_blocks` 第二段 | 副本检测沿剥噪后无有义指令的纯胶水块续查；链上命中（深度>0）允许无终结符副本组中间块 |
| 属地继承守卫 | `_block_matches_other_finally_signature` | 命中**其他** try 的 finally 体签名 ⇒ 停止吸收/登记（副本搜索、Pattern-A 走查、cleanup 走查三处共用） |
| 副本谱系结算 | `_settle_unclaimed_finally_copies` | 无主块命中唯一 finally 签名 + 终结跳转 + 出口可达 ⇒ 登记为该 region 副本；try_blocks 成员命中他区签名 ⇒ 降级移交 |
| 台账优先重建 | `analyze()` block_to_region 重建 | 两 TryExceptRegion 争抢时，finally_copy_blocks 台账持有方胜出 |
| 宿主链守卫 | `_b142_reaches_foreign_try_block` | try_start 之前的 pre-try 块若前向可达他区认领块（宿主序言链），不参与 pre-handler 扩张 |
| 声明跨度入范围 | `TryExceptRegion.get_offset_range` | range 纳入 try_offset_start，恢复嵌套 try 的层级包含判定 |
| If 候选后代剔除 | `_build_region_hierarchy` | IfRegion.blocks ⊆ child.blocks 的 If 候选不作父（其 entry 同时是外层 try entry 的形态） |
| try 体出口臂守卫 | `_b142_arm_exits_via_finally_copy` | 条件块真臂是 fc 台账成员 ⇒ try 体控制流出口形态，拒绝 match 识别（两处扫描共用） |
| fc 前置抑制门 | `_generate_block_statements`（单一漏斗） | fc 台账成员块只余控制流：回边（非循环指定 back_edge_block）→ Continue；跳出循环块集 → Break；其余 → 空发射 |
| 臂尾副本链物化 | `_process_if_blocks` | 臂末块沿 fc 成员链走到终结符，物化 Continue/Break（排除循环指定自然回边块） |

### 影响面（族覆盖的形态）

- 双层/三层嵌套 `try/finally`（B142 本形、G3 探针组）
- try 体内 `continue`/`break` 穿一/双层 finally（G2 探针组；B208 同族）
- 内层 finally 正常/异常路径顺序（G1 探针组）
- `try` 体出口 `if` 的 match 误判（B181「Continue 形态整条未产出」的伴生形态）

### 已知未封闭成员（不属本 Task 验收，挂账后续）

- `g2_brk`（break 出口 + 双层 finally + else 臂）：continue 形已绿，break 形需条件
  识别支持「一分支纯循环出口终结」归约（上游 [R13-A3] 扩展当前 TEMP-DISABLED）。
- `g3_three_fin`（三层 finally + continue）：内层 continue 物化位置尚偏。
- try 体 `return` + finally 延迟 return：**Task 4.4**（FZ-semantictrap-023 / B207，
  与本 Task 共享 finally 谱系判据）。
- p4_nest_plain（嵌套 try/finally 无控制流，内层体真实语句）：部分改善，未全绿；
  与 Task 4.4/后续族共用判据面。

## 二、探针组（Task 2.5）

| 组 | 文件 | 覆盖 | 字节级验证（冻结比较器 `pyc_verify.py single`） |
|---|---|---|---|
| G1 内层 finally 正常/异常路径 | `p_g1_fin_paths.py` | 正常出口副本序、异常传播内层→外层 | 3/3 PASS |
| G2 continue/break | `p_g2_loopctrl.py` | continue 穿双层（绿）、break 穿双层（挂账）、continue-in-except 对照（绿） | 2/3 |
| G3 双层/三层 finally | `p_g3_double_fin.py` | 双层+continue（绿）、三层+continue（挂账） | 2/3 |

B142 本形探针：`adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b71_face.pyc`
——冻结比较器 4/4 PASS（修复前 3/4，`v_nest_fin_continue` "Different control flow"）。

## 三、R1 对拍读数（Task 2.4）

`_b142_r1_check.py`（原件 marshal 加载 vs 产物 compile+exec，返回序列逐项比较）：

```
v_nest_fin_continue([0,1]): orig=[1, 2, 1, 2, 1] prod=[1, 2, 1, 2, 1] PASS
v_nest_fin_continue([1,2]): orig=[1, 2, 1, 1, 2, 2] prod=[1, 2, 1, 1, 2, 2] PASS
（另含 [], [0], [1], ([0,1],[1,0]), [5], [2,3] 共 8 组，全部 PASS → R1_RESULT=EQUAL）
```
