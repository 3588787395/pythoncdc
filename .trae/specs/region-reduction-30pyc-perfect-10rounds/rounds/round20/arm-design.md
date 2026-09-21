# Round 20 设计（arm-design）：R20-A `for` 体内裸 `break` 桩的 break-target 识别 ＋ W15-C 臂尾终止守卫

## 一、症状与目标

同一模块源码在语料里出现两份（孪生 pyc），各自唯一真缺陷都是
`<module>.RotatingFileHandler.perform_rollover`，尺子报 `[seq_len]` 少 2 条：

```
site-packages/IQCommon/logger/handlers.pyc        官方 17/18  严格 28/30（两处：perform_rollover 119→117
                                          ＋ TWHThreadController._target 192→190，后者是上一棒已登记的独立残差）
site-packages/IQEngine/utils/logger/handlers.pyc  官方 13/14  严格 16/17（唯一缺陷 perform_rollover 127→125）
```

真实源码形状（`D:/Temp/r20/scratch/recon_A.py` 重编译后与原始逐条相同，130 条原始 / 119 条去噪）：

```python
for x in range(self.backup_count - 1, 0, -1):   # FOR_ITER@102，出口 198
    if os.path.exists(src):                     # 块104，POP_JUMP_IF_FALSE@190 → 196 latch
        break                                   # 块192 = [POP_TOP, JUMP_FORWARD→302]
else:
    rename(...); self._open('w'); return        # 块198
for i in range(x, 0, -1):                       # 块302(preheader) + FOR_ITER@336 → 出口 556
    ...
rename(...); self._open('w')                    # 块556（与 198 同文本的第二份拷贝）
```

两孪生多重集差里只有两条 orig 独有且 decomp 无对应体的跳跃：`JUMP_FORWARD→302`（break 本身）
与 `JUMP_BACKWARD→102`（外层循环回边）⇒ delta 恰好 −2（`D:/Temp/r20/logs/missA.txt`）。

## 二、两层根因（缺一不可）

**① 分析层 `core/cfg/region_analyzer.py::_collect_natural_loop_body`（定义于 6101）
的 break-target 判别 6172-6175。** 两条既有判据对本形状都判 False：

* 6172 `_bt in _exit_reachable`：`_exit_reachable` 只有 `{198}`，而 198 以 RETURN 终止、无后继；
* 6174 `_bt not in _fwd_candidates`：6140-6154 的 BFS 从 `fall_through=104` 出发**会穿过 break 块
  192 自身的无条件跳转**，于是 302 被登记成「循环内前向块」。

⇒ `_break_targets = ∅` ⇒ 6186 的「以 break 目标为屏障重建」被跳过 ⇒ 6258 落到
`_cand in _return_reachable` 分支：以 556 的 RETURN_VALUE 为种子沿前驱回溯
556←336←{302,428,556…}，把 `302/336/396/428/556` 全部吞进外层 `body_blocks`
（实测 `region_analyzer.py` 输出 `has_break=False`、`break_blocks=[]`、
`body_blocks=[102,104,192,196,302,336,338,396,428,556]`，`D:/Temp/r20/logs/regA.txt`）。

**② 生成层 `core/cfg/region_ast_generator.py::_if_generate_normal` 的 W15-C
「then-独占 merge 块并入 then 臂」（16988-17004）。** `sys.settrace` 实测发射点
（`D:/Temp/r20b/logs/callsite_ca1.txt`）：

```
blk=302  _mark_with_exit_return_explicit via
   _generate_block_statements:41563 <- _if_generate_normal:16999 <- _generate_if:11112
   <- _generate_region:3046 <- _loop_handle_child_region_entry:10654
```

`:16934-16942` 已经在同一层次按 `('Continue','Break','Return','Raise')` 把臂截断到终止语句，
`_process_if_blocks:20541` 用同一集合做「终止后不再发射块」，**只有 16988 漏用**，
`:17004` 仍无条件 `then_stmts = _kept + _merge_then_stmts`。
⇒ 只修①时循环后代码被缩进在 `break` 之后 ⇒ CPython 3.11 编译器死代码消除 ⇒ 119 塌到 50
（镜像 `c_a1`，`D:/Temp/r20/logs/twin_all2.txt`）。**上一棒把 117/50 的塌方归咎于分析器，
本轮实测推翻：分析器结果是对的，塌方在生成器。**

## 三、被实测否掉的候选（镜像核，仓库零写入）

| 候选 | 规则 | 孪生 A / B | 全量 402 条目逐函数 A/B |
|---|---|---|---|
| `c_a1` | 只改分析器（宽判据，无 POP_TOP 要求） | 50 / 52（死代码消除塌方） | improved 0 / **broken 1** / signature-only 2 |
| `g1` | 只改生成器 | 117 / 125（break 仍未识别，无效） | improved 0 / broken 0 |
| `f1` | 两半都改，但②的分析器判据放宽成「恰好一条无条件前向跳转」 | 119 / 127 | improved 2 / **broken 1**（`slippage.create_new_price.check_and_return` 19→18）|
| **`f3`＝R20-A** | 两半都改，①要求桩内 **≥1 条 POP_TOP** | **119 / 127** | **improved 2 / broken 0 / signature-only 0** |

`f1` 弄坏 slippage 的形状（`D:/Temp/r20b/logs/slip_cfg_base.txt`）：块 124 = `[JUMP_FORWARD 130]`，
是链式比较 `numbers[i] <= value < numbers[i+1]` 的 out-of-line 臂桩，**没有迭代器可弹**、
语义上也讲不出 break（该处无循环可退出）。⇒ `POP_TOP` 是本判据的必需组成部分，
不得「简化」掉（`g1b` broken=0 同时证明生成器守卫单独无害）。

已排除（`ANALYSIS.md` §3）：Break/Continue 发射层丢指令（base 核下该函数的 Break/Continue
发射点命中 **0 次**）；上一棒 `region_ast_generator.py:20604` 的 `continue`→`break` 补丁
（与 `c_a1` 产物逐字相同）；名字/常量/原始偏移匹配型规则（mandate 禁止，本提案两处均纯结构判据）。

## 四、修法（两处，各自同层次、同判据）

**(a) 分析器**：把 6172-6175 的 `if/elif` 改写成三析取项的单个 `if`，追加第三条**结构**析取项
`_r20_is_break_stub_block(_bb)`——`_bb` 就是 6156 循环里已有的块变量，不新增遍历维度：

```python
                                if (_bt in _exit_reachable
                                        or _bt not in _fwd_candidates
                                        or _r20_is_break_stub_block(_bb)):
                                    _break_targets.add(_bt)
```

谓词（模块级，`class BlockRole` 之前）：去噪（NOP/CACHE/EXTENDED_ARG/PRECALL/RESUME）后
= **≥1 条 `POP_TOP` ＋ 恰好一条无条件前向跳转**。

**(b) 生成器**：复用既有臂尾终止判据，不新建谓词：

```python
        if (getattr(region, 'merge_block', None) is not None
                and self._merge_block_is_then_exclusive(region)
                and not (then_stmts
                         and isinstance(then_stmts[-1], dict)
                         and then_stmts[-1].get('type') in
                             ('Break', 'Continue', 'Return', 'Raise'))):
```

跳过后 merge 块不再被标 `generated`，由外层区域序列正常发射 ⇒ 循环后代码回到函数层级。

**四条区域归约原则核对**：(a) 只是把已存在的 break 出口登记为 break，内层→外次归约次序不变、
不新增区域嵌套；(b) 只是**取消**一次跨层次拼接，让 merge 块回到本来的父区域层级 ⇒
「每块唯一归属」「嵌套区域在父层是单一抽象节点」「父层列表只引用子区域入口块」均未被触碰。
禁止跨区域跨层次启发式：两处判据都只读同层次的块内指令形状 / 同一臂的末条语句类型。

## 五、门禁计划（按 mandate 顺序，逐条有实测数值才算通过）

1. 落地 R20-A（字节级补丁器：BOM／纯 CRLF／锚点唯一／`ast.parse`／拒绝二次应用）。
2. 单点必须修到完全 OK：`single` ＋严格尺子复验孪生 B（`perform_rollover` 127/127、
   严格 17/17、`decompile_status: ok 14/14 100.00%`），再验孪生 A（119/119、`ok 18/18 100.00%`，
   `_target` 必须仍是 192/190 的原样残差）。
3. `quotation.pyc` 单验：必须与 Round 19 记录逐字相同（`partial 143/142 99.30%`、
   唯一缺陷 `change_his_to_forward: orig=547 decomp=548 jump_diffs=1 true_diffs=377`），
   且产物 `quotationOK.py` 不被改写 ⇒ 有任何差异即停下修副作用。
4. 全量产物门：`_r13_gate.py` 分 8 片覆盖 402 条目，基线 = 落地前磁盘产物逐函数严格比对
   （utf-8 写出）。异常集合必须恰为 Round 19 那 9 个文件、数值逐条相同；出现第 10 个即回滚重做。
5. 全量逐函数 A/B 归因（与门 4 分开）：`git archive <落地前 rev>` 重建 pre-landing 核镜像，
   与落地后核镜像各跑 402 条目 ⇒ improved=2（且恰为两孪生）、broken=0。
6. 电池：`test_repros/round20_rollover/run_all.py --strict` 退出码 0、`UNEXPECTED=0 ERROR=0`，
   `EXPECT` 表按落地后实测重写；既有 10 套（round13/13b/14/14_join/15_arm/16_arm/16_sink/
   17_arm/18_arm/19_cont）全部 `--strict` 退出码 0，被本修复合法修掉的锚点改标 `SENTINEL`。
7. 索引：只允许 `single` 自己写回；402 条目、每条 `function_count` 不变、Σ=5746；
   `stats` 序列 matched ≥5630、rate ≥97.98%。
8. 记录 + 提交 push。
