# R15-07 / T12-11 — 发射端臂批量认领吞掉嵌套区域语句（realtime_event_source::clock_worker）

## 1. 旧前提被实测推翻

任务卡原写「IfRegion@7972 的 then 臂为空 / 体被父臂认领」。本次在进程内做只读普查
（`D:/Temp/r150/probe_evt3.py`、`probe_evt4.py`）：

```
blocks=191 regions=67
---- blocks in NO region ----   unowned-instruction total: 0
IfRegion@7972: blocks=[7972,7980,8166] condition_block=7972
               then_blocks=[7980,8166] else_blocks=[] merge_block=8170 parent=LoopRegion@5598
blocks in [7972,8180]: [7972, 7980, 8166, 8170]      ← @7982..@8164 不是块边界
  @7980 len=25 tail=POP_TOP succs=[8166,9218]        ← 体是单个 25 指令块
```

识别端完整：@7980（25 条指令的语句块）+ @8166（return）都在 `then_blocks` 里，
「7982..8164 不在任何区域」是上一轮把字节偏移误当块边界得到的错记录。
全库 unowned 指令合计 = 0。

## 2. 缺陷在发射端认领

`D:/Temp/r150/hunk_meas.py` 对产品做指令级差分（口径：opcode+argrepr，忽略
NOP/CACHE/EXTENDED_ARG 与跳转目标）：

```
control(none)   len orig=1424 prod=1311 delta=-113 hunks=51 del=186 ins=73 bigloss=1
  BIG replace orig@1179..@1289 (del=110 ins=1)
     - @7972 LOAD_FAST persist_flag … @7980 LOAD_GLOBAL NULL+set_trade_stop_status
       … system_log.error('获取交易持久化对象超时，系统退出')
       … self.event_queue.put((dt, EventEnum.SYSTEM_EXIT)) … @8166 RETURN_VALUE
     + @7844 JUMP_FORWARD -> 8448
```

产品源码中 `set_trade_stop_status(` 只在第 13 行的 import 出现一次，调用体不存在，
`if persist_flag is False:` 整条语句不存在。

认领点（在进程内把 `generated_blocks` 换成记录型 set，取调用栈内层帧，
`D:/Temp/r150/probe_evt6.py` / `probe_evt8.py`）：

| 站点 | 位置 | 认领内容 |
|---|---|---|
| A | `region_ast_generator.py:_if_generate_normal:21290` | or-extension 臂 `for b in region.else_blocks: add(b)` —— @7972/@7980/@8166 |
| B | `region_ast_generator.py:_process_if_blocks:25339` | `for _nb in _nr.blocks: add(_nb)` 无条件认领 |

调用链证明 @7972 从未作为区域入口被分派（DISPATCH 日志为空）：它在 A、B 两处
被标成 generated，等父层块序走到它时命中 `if block in self.generated_blocks: continue`
（如 `_loop_generate_body:8295`），于是语句整条消失。

## 3. 双臂矩阵（只判 pycdc.py 产物，跑完逐字节还原 core）

| 臂 | 站点 | delta | hunks | ins | bigloss | `persist_flag is False` | `set_trade_stop_status(` |
|---|---|---|---|---|---|---|---|
| none | — | −113 | 51 | 73 | 1 | 0 | 0 |
| claimfix | A | −113 | 51 | 73 | 1 | 0 | 0 |
| nestedonly | 21324/21326 | −113 | 51 | 73 | 1 | 0 | 0 |
| pair v4（仅保护区域入口） | A+B | −52 | 51 | 134 | 2 | 1 | 0 |
| **pair v5（保护更深层未生成区域的成员）** | A+B | **−6** | 54 | 162 | 3 | **1** | **1** |

v4 只挡「b 是某未生成区域的 entry」；@7980/@8166 是 If@7972 的 **then 成员**而非入口，
所以仍被吞。v5 的判据改为：b 只要属于某个 **非 owner、且尚未生成/未在生成中** 的区域，
就不得在父层批量认领——即原则 2（每块唯一归属）+ 原则 3（嵌套即抽象节点）+
原则 4（父层只引用子区域入口）。三条语句（`set_trade_stop_status(...)`、
`system_log.error('获取交易持久化对象超时，系统退出')`、
`self.event_queue.put((dt, EventEnum.SYSTEM_EXIT))`）在 v5 产物中全部出现。

判据实现（落在 core，注释即判据本身，见 `_arm_block_pending` docstring）：
成员表 `block -> [regions]` 每实例建一次，只读结构事实与区域状态位，
不读名字/常量/绝对偏移/指令条数（rules.md §1.5 G4）。

## 4. 本单元剩余残差（不属本判据）

v5 后 clock_worker 仍非 13/13：`delta=-6`，另有两类与认领无关的形态 ——
orig `@6690`（`if holiday_not_do_before == '0': self.event_queue.put((dt,
BEFORE_TRADING_START)); self.before_trading_date = now_date`）在 control 里被搬到
循环尾（产品 291-293 行），属 **重定位** 家族；以及 `@9208 POP_JUMP_BACKWARD_IF_TRUE`
尾部三元组的插入/换位。因此本单元即使认领修好也需要第二判据；结论以 402 全量
gate 的单元翻正数为准，不以本单元 delta 缩小为准。

## 5. 事故与整改

`arm_evt4.py all` 在 restore 步骤抛 `OSError [Errno 22]`（写 3.7 MB 源文件失败）后中止，
下一次运行按其自身的 `copyfile(GEN, BAK)` 把 **已打补丁** 的文件覆盖成备份，唯一干净
副本丢失，core/ 停在补丁态。恢复来源：`D:/Temp/r150/generator.bak`
（sha256[:16] `851b0723732a2402`，与会话起始一致），还原后 `py_compile` 通过、
`git status --porcelain -- core/` 为空。整改：
1. 不可变、内容寻址的干净副本 `pristine_851b0723732a2402_region_ast_generator.py`；
2. `evt_patch.py apply` 断言打补丁前 `hash(GEN)==CLEAN_HASH`；
3. 写入带重试（4 次 × 2 s）；
4. apply/restore 后都打印 hash 与 `byte_exact=`。
该教训已写入用户级记忆 `feedback-patch-rig-crash-clobbers-backup.md`。
