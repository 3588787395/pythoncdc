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
