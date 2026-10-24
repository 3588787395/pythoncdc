# Task 4.4 finally-return（FZ-semantictrap-023 / B207）诊断笔记（续作用）

日期：2026-10-24。输入：`_r6_fuzz/FZ-semantictrap-023-cb72b56d.{py,pyc}`（由
`.trae/specs/attack-completeness-claims/rounds/round9/minimized/FZ-semantictrap-023-cb72b56d.min.py`
复制编译；工作区 scratch，不入库）。

## 现状读数

- `pyc_verify single`：1/2（return 语义单元红）。
- 产物（`_r6_fuzz/FZ-semantictrap-023-cb72b56dOK.py`）：
  ```python
  def main():
      try:
          for i in range(5):
              try:
                  pass                        # ← return ("ret", i) 丢失
              finally:
                  events.append(('fin', i))
              return events.append('outer')   # ← 错拼：finally 副本 append 被并进 return
      finally:
          events.append('outer')
  ```

## 原件字节码结构（CPython 3.11 零成本 finally 内联，dis 已核对）

```
 34 FOR_ITER → 36 STORE i
 38 NOP                      # try: 行标记（内层 try，受保护）
 40-44  LOAD_CONST 'ret' + LOAD_FAST i + BUILD_TUPLE   # return VALUE 计算
 46-104  finally 副本①：events.append(('fin', i)) + POP_TOP +
         SWAP + POP_TOP       # ★ return value 压在栈底、cleanup 在栈顶的
                              #   SWAP/POP 杂耍 = return-in-finally 形态标记
 106-158 outer finally 副本：events.append('outer') + RETURN_VALUE@158
 160-224 inner finally 异常路径副本（fin append + RERAISE）
 226  NOP + outer finally 副本（loop 耗尽路径）：append + LOAD_CONST None +
      RETURN_VALUE@282
```

## 根因假设（待验证）

try 体 walk 把「return 值计算段（40-44）」与「finally 副本①（46-104）」合并
重建：RETURN_VALUE@158 与 finally 的 append CALL@146 被拼成
`return events.append('outer')`；真正的 return 值段 40-44 被丢弃成 `pass`。
Task 2 的 finally_copy_blocks 台账（region_analyzer）已识别 finally 副本块；
缺的是 **return-in-finally 形态**：SWAP+POP_TOP（@102/104，栈底压着返回值）
是「return 值已求值、cleanup 覆其上」的结构标记。

## 修复方向（族级，I.4 白名单）

1. 在 try 体 walk（`_generate_try_body` / finally 副本归属路径）识别形态：
   `<return 值指令段>` + `[COPY/SWAP/POP_TOP 杂耍]` + `[finally 副本语句]` +
   … + `RETURN_VALUE`（嵌套 finally 时多层副本串联）。
2. 归约：return 值段重建为 `return <value>` 置于 try 体；副本段由既有
   finally 机制再生（Task 2 已验证 byte-equal）；副本尾的 RETURN_VALUE 由
   `return` 语句重编译自然再生（不再显式发射 append+return 混合体）。
3. 判据只读：异常表（finally 区间）、栈杂耍 opcode 形态（SWAP/POP_TOP）、
   RETURN_VALUE 归属——无名字/偏移特判。
4. 验证：023 → 2/2；x01/v_b71/G 探针/402 shard0/small34 无回退；注意与
   Task 2 B142 台账共享 finally 谱系判据，勿双重登记。

## 关联文件

- 修复点预估：`core/cfg/region_ast_generator.py` try 体装配路径（34xxx
  `_generate_try_body` 一带）与 finally 副本发射（`_b142_*` 谱系）。
- 复现命令：`python -X utf8 pycdc.py -o _r6_fuzz/FZ-semantictrap-023-cb72b56dOK.py
  _r6_fuzz/FZ-semantictrap-023-cb72b56d.pyc`。

## 七、实现与验证终态（2026-10-24 第二轮）

**已落地（280d2c59）**：`_b207_return_in_finally_stmts` 挂入 `_generate_try_body`
块循环（B75 认领后、fc-keep/B119 前）。判据：①值运行无语句终结符且可重建；
②直落链（start_offset == 末有效指令偏移+2，≤8 跳）逐块为 finally 异常副本体的
指令级同构切片（B75 同词汇；finally_copy_blocks 台账对此形态为空）；③链尾
RETURN_VALUE 终结且 RETURN 前运行可重建。归约：值尾块发射 `Return(值)`，副本
链 + 链尾块登记 generated（副本由各层 Try finalbody 机制再生）。
**条件臂守卫**：值块被前驱条件跳转指入（`if c: return V` 臂）时不归约（无条件
Return 会吞 if 条件——023 全量实测）。

- 最小复现（minimized）FZ-023：**pyc_verify 2/2**，产物与原件源码形态逐字一致。
- 回归：402 shard0 786/786、small34 1568/1568、B142 定向全部持平冻结基线、
  pytest 失败清单与 406 项基线逐字节一致。

## 八、残余挂账（fuzz 复跑 21/24 EQUAL）

| case | 现象 | 根因 | 归属 |
|---|---|---|---|
| FZ-semantictrap-023（全量） | `if i == 1: return ("ret", i)` 条件臂 return-in-finally：if 臂装配路径缺同型归约，臂内值运行被丢（`pass`） | 条件臂守卫正确拒判后，if-then 臂装配无 return-in-finally 处理 | B207 条件变体，挂账 |
| FZ-deephost-001 | strict R7 co_code.len 414→416：match `case _` 臂首 NOP 被行头游程解析按队列假值单元多发 1 NOP（pyc_verify 2/2） | case 臂首 NOP 是 match 语句再生锚点，队列未引用 0 误配假值单元；实测：锚点完全丢弃 → 臂装配坍缩（更糟），裸 Pass 分支亦坍缩——臂装配依赖游程单元的机制未明 | [B207-邻域] match 臂锚 × 游程解析交互，挂账 |
| FZ-raresyntax-015（全量） | strict R7 co_code.len 72→68（-4） | 全量形态常数列表编译形差（`[3,4,5,6]` 直落 BUILD_LIST vs 原件 BUILD_LIST 0+常量元组+LIST_EXTEND 常量列表优化形），最小复现已 2/2 | 常量列表编译形保真族，挂账 |

去重判定：三者均不新增 B 编号——023 条件变体与 deephost 残余归 B207/B142
finally 谱系，015 全量残差归常量列表编译形（与 B203 值丢失不同机制），维持既有
编号。Task 4.6 目标 24/24 未达（21/24），不得宣称封闭。
