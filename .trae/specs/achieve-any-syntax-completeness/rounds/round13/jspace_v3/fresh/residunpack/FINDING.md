# rr-v5r153 [v153-RESIDUNPACK] 链式元组解包残栈值源族（六语句位形全闭合）

## 功效案（六个语句位形，全部 HEAD-TEXT-DIFF→v153 JUDGE-EQUAL 字节验证）

`(a, b), (c, d) = x, y` 编译为 `LOAD x; LOAD y; SWAP 2; UNPACK 2; STORE a;
STORE b; UNPACK 2; STORE c; STORE d`——首解包值=reconstruct 栈顶（SWAP 后 TOS），
**残栈元素（y）是紧随 UNPACK 的值源**。全部解包状态机丢弃残栈 → 第二 UNPACK 空缓冲
value=None → 第二目标对静默丢失、名字落 LOAD_GLOBAL（真实 R1：c/d 未定义）。

| 位形 | 宿主状态机 | 修复前渲染 |
|------|-----------|-----------|
| E1 函数顶/块体 | `_generate_block_statements_body` `_ua_unpack_stack` 机 | `a, b = x` |
| E2 while 体内 | `_loop_extract_self_loop_stmts` `_sl_unpack_info` 机 | `a, b = pairs[total]` |
| E3 for 体内 | `_generate_stmts_from_instrs`（`_gi` 机） | for 整体退化 |
| E4 if 体内 | `_ua` 机（then 臂） | `a, b = x` |
| E5 if/else 后序列 | `_ua` 机 | `a, b = x` |
| E6 while 后序列 | `_ua` 机 | `a, b = xs[0]` |

（difflib._line_wrapper 的 while 前缀位形由 r152 的 v152-DUALUNPACK2 已闭合；本轮
补齐其余六位形 + `_fu_` 路径（`_build_effective_stmts`，fix152d.py 重放）。）

## 修复（只增不破，generator 单文件）

每台状态机同一模式（v152-DUALUNPACK2 同族外推，七台全覆盖）：

1. **残栈 pending 队列**：有值缓冲的 UNPACK 走既有 reconstruct 后捕获残栈
   （非 PUSH_NULL 元素、TOS 在前）为 `_v153_dual_pending`；
2. **空缓冲取值**：紧随的 UNPACK 缓冲为空且队列非空时从队列取值
   （`_v153_from_residual=True`）；
3. **合并发射**：首帧完成处后随指令直接是 UNPACK_* 且队列非空时持存
   （不立即发射）；链帧完成时若其值来自残栈则与持存帧合并发射单条
   `Assign(targets=[Tuple([首对, 链对])], value=Tuple([首值, 链值]))`
   （TOS 在前=源级元组序）——重编译经同一 SWAP+多 UNPACK 形再生（字节等价）；
4. **守卫**：独立连续解包（链帧有自己的值缓冲）、嵌套链（`(a,(b,c))=x` 的子帧值
   不入发射）、星号/属性/下标目标、walrus、任何收集不全或残栈数不符——逐位落回
   既有路径。

七台状态机：`generate()` `_entry_unpack_info`、`_loop_generate_while`（r152 已修）、
`_loop_extract_self_loop_stmts`、`_loop_process_header_instructions`、
`_loop_extract_pre_stmts_from_instrs`、`_generate_stmts_from_instrs`、
`_generate_block_statements_body` `_ua_unpack_stack` + `_build_effective_stmts`
`_fu_` 路径。

## 验收

- 六复现案判官全部 Equal/Equal（R1-R6）
- difflib 判官 **62/62 = 100.00% 维持**（difflib_judge_v153.txt）
- 矩阵 19 案 ALL PASS（E1-E6 功效案 HEAD TEXT-DIFF→v153 JUDGE-EQUAL；C1 独立连续
  解包/C2 单解包/C3 嵌套/C4 星号/C5 walrus/C6 属性目标 W19/C7 下标目标/C8 mdiff3/
  C9 latch_if/C10 line_wrapper 全形/C11 fancy_tail/C12 na5 全 SAME+JUDGE-EQUAL；
  C13 B116 SAME 预存在 DIFF 维持）
- 电池 341 案（R110 169 + V111..V153 累计 + V153 19）——r153_regress_result.txt
- pytest 2F/277P/2XP 冻结基线
- REAL46 全量 sweep 小修口径豁免

## 文件

- matrix_v5r153.py / matrix_v5r153_result.txt（r153matrix）
- r153_regress.py / r153_regress_result.txt
- difflib_judge_v153.txt
- fix153.py（四台状态机）/ fix153b.py（_ua 机）/ fix153c.py（_gi 机）/ fix152d.py（_fu_ 重放）
- fix_patch_v5r153.diff
- 复现存档：r153probe/R1-R6（probe_resid.py 生成）
