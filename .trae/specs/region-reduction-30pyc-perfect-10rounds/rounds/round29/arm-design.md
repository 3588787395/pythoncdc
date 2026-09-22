# Round 29 arm design — R29-A：原则 2「每块唯一归属」的臂间共享块取消认领

## 靶子（实测，非读码猜测）

`site-packages/fly/dumpload/load_daily.pyc :: <module>`，落地前官方尺
`mism=[['<module>', 913, 913, 1, 19]]`——**指令数完全相同、只有一个跳转槽不同**，
是该文件唯一缺陷（22/23，deficit 1）。严格尺读数为 `seq_diff`（整段错位），首处分歧在
orig `#596 JUMP_FORWARD 2478` 对产物同槽 `PUSH_NULL`；orig 的
`[JUMP_FORWARD→2478, PUSH_NULL, LOAD_NAME print, LOAD_CONST 'ERROR:…', CALL 1, POP_TOP]`
六条逐字重现在产物 `#611`（@2538）——同形块换位，不增不减。

## 取证链（全部为镜像打戳实测，禁止读码下结论）

1. **11 处 `merge = else_succ` 全数打戳**（`D:/Temp/r29gate/mkstamp29c.py`，arm `stamp`）：
   命中 8 次，落点为 1116/2768/960/796/686/472/472/368，**没有一次涉及 2478**
   ⇒ 汇点塌缩（R13c/`_25b`）与本轮无关。第一版戳因 `%s` 少一个占位符而整轮抛
   `not all arguments converted`，戳不落盘≠没有命中，修好后才得到上面的读数。
2. **Round 28 判据的邻位假设否证**：`_cr.then_blocks.append(_sb)`
   （`region_analyzer.py:1847`，IF_ELIF_CHAIN shared_block 后处理）打戳（arm `p29c`）：
   append 站点那把戳（P2）**0 次命中**（`grep -c R29P2 = 0`，即日志里单独那行 `0`），
   而其循环头那把（P1）确有 4 次读数 `sb=370/390/582/288`——**无一次为 2478**；
   且该臂产物读数与落地核逐字节相同（913/913/1/19）⇒ 双重认领不发生在 shared_block 后处理。
   （若两把戳都无读数便是探针坏了，不是没有命中——见第 1 条的同型事故。）
   诊断代理 B 的第二把戳独立复现同一 0 命中，两条线合流。
3. **构造点打戳**（`D:/Temp/r29gate/mkp29d.py`，arm `p29d`，三处 `region = IfRegion(` 之前
   + 生成端 `_process_if_blocks(region.then_blocks, …)` 消费点之前，均以 2478 为门）：

```
[R29D1] site=17888 cfg=<module> entry=740 merge=2626 else=[2456, 2478, 2562]
                     then=[954,1072,1116,1096,1112,1254,1278,1338,1442,1556,1702,2198,1932,2022,2478,2086,2176,2562]
[R29D2] FINAL 同上（生成端消费时集合未变）
```

⇒ **2478 与 2562 同时出现在同一个 IfRegion 的 then 臂和 else 臂里**，即构造当场就双认领；
既有的「IF_THEN merge 候选识别」（`region_analyzer.py:17850-17878`）整段被
`if merge is None and not else_blocks` 挡在门外（本例 merge=2626、else 非空），
而它自己的注释早已写明「then_blocks 包含 merge 块 ⇒ AST 生成错误」。
生成端 `_process_if_blocks` 对每条臂按 `start_offset` 升序遍历，于是 then 臂抢在
else 臂之前发射了 if/else **之后**的语句块 2478，实测即上述换位。

## 判据

同一 IfRegion 的两条臂是互斥控制流路径：一个块不可能既是 then 体又是 else 体。
被两臂同时认领的块只能是由两臂共同到达的汇合点（merge/join），它按定义位于两臂入口之后，
任何一臂把它当作体内块都是越界吸收。故在 `IfRegion(...)` 构造边界之前取消 then 臂对
`set(then_blocks) & set(else_blocks)` 的认领：

```python
if then_blocks and else_blocks:
    _arm_shared = set(then_blocks) & set(else_blocks)
    if _arm_shared:
        then_blocks = [b for b in then_blocks if b not in _arm_shared]
```

同层性：只读块自身的归属状态（两条臂列表的交），不读偏移常量／名字／条数／函数名。
只删不增：`all_blocks = all_condition_blocks | set(then_blocks) | set(else_blocks)`
是两臂之并，从 then 臂摘出不丢失任何块，只是取消双重认领；发射端不新增任何规则，
不命中时行为逐字节不变（G4 的 SAME=401 即此断言的全量证据）。

落点选择理由：这是**唯一**同时满足「离缺陷构造当场最近」与「不改变 merge 指向」的位置——
把 2478 改设为该区域的 merge 会连带改动区域 exit（实测 merge=2626 是父序列继续走所需的落点），
属于跨区域的语义变更，本轮不做。

## 已知边界（诚实记录）

* 取消认领后 2478 仍留在 else 臂里，产物把该语句显示在 `else:` 内。官方尺判 23/23 全匹配，
  严格尺由 `seq_diff` 改善为 `target_diff`（σ 两侧都是 0，clean 22/25 不变）：跳转目标
  仍与 orig 差一格。即本判据修复的是**发射次序**，不修复**源级嵌套归属**，后者是
  同一函数的残余线索，移交后续轮次。
* G0 语料外最小复现**未取得**：把落地核产物与候选核产物各自 `.py` 再编译成 `.pyc`
  回灌，两把尺都是 23/23 全匹配（`r29a_03/r29a_04` 实验）——本族的缺陷在「原始字节码布局
  被分析器双认领」，不存在一个能复现它的源级合成文件。已改为交付
  `test_repros/round29_arm_shared_join_claim/r29a_01_shape_mimic_and_controls.py`
  （形状仿写＋三条 CONTROL，实测在落地前后均为 2/2 匹配，充当判据的非触发面）
  ＋ 语料靶子本身的严格尺证据链。顺带暴露的 `r29x_01_module_if_deficit_witness.py`
  （`<module> 142/138`，两把尺同形失败）是另一条线的语料外复现，随本轮移交。
