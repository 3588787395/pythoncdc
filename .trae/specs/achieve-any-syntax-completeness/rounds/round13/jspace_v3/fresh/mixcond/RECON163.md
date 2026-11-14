# RECON163 — rr-v5r163 只读侦察：`FTPHandler.ftp_open` / `URLopener.retrieve`

- 仓库：`F:\Downloads\pythoncdc-main`（只读，未改任何仓库文件）
- 解释器：`D:/Python/python.exe`，全部命令 `-I -X utf8`，cwd=仓库根
- 产物目录：`D:\temp\opencode\cl_layout\r163\`
- 判官：`scripts/pyc_verify.py single <pyc> --source <out>`（唯一判据 pylingual `compare_pyc`）
- 当前整模块：`request_now.py`，判官 `status=failure units=192/194 success_rate=98.97%`，仅两单元失败，均 `Different control flow`：
  - `FTPHandler.ftp_open`
  - `URLopener.retrieve`

---

## 1. 形态对照表

### 1.1 `FTPHandler.ftp_open`

| 项 | 内容 |
|---|---|
| 真实源码（`D:/Python/Lib/urllib/request.py:1566-1567`） | `type = file and 'I' or 'D'`<br>`for attr in attrs:` |
| 当前产物（`request_now.py:1119-1120`） | `type = file and 'I' or 'D'`<br>`for attr in file and 'I' or 'D':` |
| 判官 | `Failure: Different control flow` |
| 错误性质 | for 的 iterable 被换成上一条赋值语句的完整 BoolOp 值；真正的 iterable `attrs` 丢失 |

关键点：`type = ...` 这一行在实模块产物里**仍在**（由并存的 TernaryRegion 发射，见 §3.1），但 `for` 的 iterable 仍然错成同一条链。最小复现中该赋值行会直接消失（LoopRegion 抢先认领 BoolOpRegion），属于同一错误谓词的另一种可见形态，不是另一个根因。

### 1.2 `URLopener.retrieve`

| 项 | 内容 |
|---|---|
| 真实源码（`request.py:1813-1820`） | `if filename is None and (not type or type == 'file'):`<br>`    try:`<br>`        fp = self.open_local_file(url1)`<br>`        ...`<br>`    except OSError:`<br>`        pass` |
| 当前产物（`request_now.py:1302-1314`） | `if filename is None and type:`<br>`    if type == 'file':`<br>`        pass`<br>`    else:`<br>`        fp = self.open(url, data)`<br>`    try:`<br>`        fp = self.open_local_file(url1)`<br>`        ...`<br>`    except OSError:`<br>`        pass`<br>`fp = self.open(url, data)` |
| 判官 | `Failure: Different control flow` |
| 错误性质 | 守卫混合链 `A and (not B or C)` 被压平成 `A and B and C`（并叠加错误的 else 分支/重复 `open`）；`not` 与 `or` 分组丢失，`type` 为假时本应进入本地文件分支，产物却跳过 |

最小形态（`mx2_b`）只保留守卫即失败，证明条件本身足以触发，不依赖外层双层 try/finally：

```python
# mx2_b_src.py
def f(filename, type):
    if filename is None and (not type or type == 'file'):
        x = 1
    return 0
```

产物（`mx2_b_out.py:5`）：

```python
if filename is None and type and type == 'file':
```

---

## 2. 最小复现清单

全部位于 `D:\temp\opencode\cl_layout\r163\`；每个都有 `_src.py`、`.pyc`、`_out.py`。判官日志见 `judge_log.txt`。

| 文件 | 复现形 | 产物错误行 | 判官 |
|---|---|---|---|
| `mx1_a` | `x = file and 'I' or 'D'` 紧接 `for attr in attrs` | `mx1_a_out.py:5` `for attr in file and 'I' or 'D':` | failure / Different control flow |
| `mx1_b` | 改名版（`a/b/x/y`） | `mx1_b_out.py:5` `for y in a and 'I' or 'D':` | failure |
| `mx1_c` | 只保留 `a and 'I'`（无 or） | `mx1_c_out.py:5` `for y in a and 'I':` | failure |
| `mx1_d` | 只保留 `a or 'D'` | `mx1_d_out.py:5` `for y in a or 'D':` | failure |
| `mx1_e` | 赋值前再加一条 `z = g(attrs)` | `mx1_e_out.py:6` 同样的错误 for | failure |
| `mx2_a` | 守卫 + 内层 `try/except OSError` | `mx2_a_out.py:5` 压平条件 | failure |
| `mx2_b` | 仅守卫 + 赋值体（最小失败形） | `mx2_b_out.py:5` 压平条件 | failure |
| `mx2_c` | 同 `mx2_b`，但体为 `pass` | `mx2_c_out.py:5` 仍压平 | **success（判官盲区，勿作正确性依据）** |
| `mx2_d` | `and (type or type == 'file')`（无 not） | 正确保留 | success |
| `mx2_e` | `and not type`（无 or） | 正确保留 | success |
| `mx2_f` | `and (not type or other)`（or 另一变量） | `mx2_f_out.py:5` 压平成 `and type and other` | failure |

削减结论：

- `ftp_open` 族不要求 `and/or` 混合，也不要求上一条是混合链：**任意 BoolOp 赋值语句紧接 `for`，且该 BoolOp 的 merge 块同时承载 for 的 setup** 即可触发（`mx1_c`/`mx1_d`）。
- `retrieve` 族要求 **`not B or C` 作为外层 `and` 的非首成员**：`(B or C)` 正常（`mx2_d`），单独 `not B` 正常（`mx2_e`）；`not B or other` 同样失败（`mx2_f`），说明与 `type == 'file'` 这个具体比较无关，关键在 `not ... or ...` 的极性。
- `mx2_c` 判官 success 是“体为空”导致的控制流等价盲区；产物条件仍然是错的，不能据此判定该族已修好。

判官逐条记录（节选）：

```text
===== mx1_a =====
  ***<module>.f: Failure: Different control flow
[single] status=failure units=1/2 success_rate=50.00%
===== mx2_b =====
  ***<module>.f: Failure: Different control flow
[single] status=failure units=1/2 success_rate=50.00%
===== mx2_c =====
[single] status=success units=2/2 success_rate=100.00%
```

---

## 3. 根因定位（dis + 运行时探针）

### 3.1 `ftp_open`：for-iterable 在块粒度上越过了上一条语句的边界

#### 字节码（`D:\temp\opencode\cl_layout\r163\ftp_open.dis`）

```text
1566  686 LOAD_FAST            12 (file)
      688 POP_JUMP_FORWARD_IF_FALSE     2 (to 694)
      690 LOAD_CONST            7 ('I')
      692 JUMP_IF_TRUE_OR_POP      1 (to 696)
1567  694 LOAD_CONST            8 ('D')
      696 STORE_FAST           14 (type)     ← 上一条赋值的值写回
      698 LOAD_FAST            10 (attrs)    ← for 真正的 iterable
      700 GET_ITER
      702 FOR_ITER             68 (to 840)
```

对应块（`probe_regions.py`）：

```text
B25: 696 STORE_FAST type
     698 LOAD_FAST attrs
     700 GET_ITER
LoopRegion: for_iter_setup = B25 (696-700)
BoolOpRegion: blocks=[624,690,694,696]
              op_chain=[(624-688,'and'), (690-692,'or')]
              merge_block = B25 (696-700)
              value_target = 'type'
```

#### 结论：不是“语句层复制整条链”，也不是普通的“iterable 提取读错栈”

- 上一条赋值 `type = file and 'I' or 'D'` 的 BoolOpRegion **merge 块就是 B25**；而 B25 在字节码里继续包含下一条语句的 `LOAD_FAST attrs; GET_ITER`。
- `_loop_generate_for` 用 **merge 块身份**判定“该 BoolOp 就是 for 的 iterable”：
  - `core/cfg/region_ast_generator.py:8026-8032`：`_r.merge_block is for_iter_setup` 即选中 `_boolop_for_iter`；
  - `:8080-8092`：直接把整个 BoolOp 表达式作为 `iter_expr`，并把链块标记为已生成；
  - `:8093` 的 `if iter_expr is None ...` 因此不成立，指令级的 `_loop_extract_for_iter_pre_stmts`（`:12033`，本可把 `type = ...` 前缀和 `LOAD attrs; GET_ITER` 分开）被整段跳过。
- 所以这是 **for 的迭代器提取在“基本块”粒度上越过了语句边界**：B25 同时承载“上一条赋值的收尾 STORE”和“本 for 的 iterable 装载 + GET_ITER”。BoolOpRegion 的 merge 块只表示“值在这里汇合”，并不表示“这个值被 GET_ITER 消费”。
- 同一谓词在 `_generate_boolop` 还有一份镜像：
  - `core/cfg/region_ast_generator.py:53004-53010`：`not _is_outer_condition and not is_condition_context and LoopRegion.for_iter_setup is region.merge_block` → 标记链块、写入 `condition_expr`、返回 None。
  - 本模块实测走的是 `_loop_generate_for` 分支（探针只打印 `[loop] entry=702 fis=696 boolop_hits=[...]`，没有打印 `[boolop]` 命中）。两处都假设“merge == setup ⇒ 该 BoolOp 是 iterable”，修复时需同时加门。

#### 为什么实模块还保留了 `type = ...`，而最小复现把它吞掉了

运行时探针（`probe_emit2.py`）显示，实模块同一段链上还并存一个 TernaryRegion：

```text
[ternary] merge=696 target='type' -> [(['fw'], 'Call'), (['type'], 'BoolOp')]
```

它先发射了 `fw = self.connect_ftp(...)` 和 `type = file and 'I' or 'D'`；随后 LoopRegion 又用同一个 BoolOpRegion 作 iterable。最小复现没有这条前置 `fw = ...` 语句，TernaryRegion 未成立，LoopRegion 独占该 BoolOpRegion，于是赋值行消失。两种表现共享同一个错误谓词（`merge_block is for_iter_setup` 被当成“iterable 就是它”），不是两个根因。

#### 直接回答题干

- **不是**语句层把整条链当值表达式“复制”了一份；`type = ...` 的发射来自 TernaryRegion/语句路径。
- **是** for 语句的 iterable 提取在块粒度上越界：它没有从 `GET_ITER` 之前只取 `LOAD_FAST attrs`，而是把同块内上一条语句的 BoolOpRegion 整体当成了 iterable。
- 关键块与偏移：**B25 = 696-700**；BoolOp 赋值链 686-696；真正的 iterable 装载 698-700；`FOR_ITER` 在 702。

---

### 3.2 `retrieve`：`A and (not B or C)` 的守卫链极性/目标判错

#### 字节码（`D:\temp\opencode\cl_layout\r163\retrieve.dis`）

```text
1813 152 LOAD_FAST                2 (filename)
     154 POP_JUMP_FORWARD_IF_NOT_NONE 122 (to 400)
     156 LOAD_FAST                5 (type)
     158 POP_JUMP_FORWARD_IF_FALSE     6 (to 172)   ← 假边进入 body(172)：这是 not type
     160 LOAD_FAST                5 (type)
     162 LOAD_CONST               2 ('file')
     164 COMPARE_OP               2 (==)
     170 POP_JUMP_FORWARD_IF_FALSE 114 (to 400)    ← 假边进入 merge(400)
1814 172 NOP                                        ← then body
...
1821 400 LOAD_FAST                0 (self)          ← merge / 后续语句
```

块布局：

```text
B1 (0-4):   filename is None 测试（IF_NOT_NONE → 400）
B2 (6-8):   type 真值测试（IF_FALSE → 172 body）
B3 (10-20): type == 'file'（IF_FALSE → 400 merge）
B4 (22-24): 赋值体 x = 1
B5 (26-28): merge / return
```

`probe_regions.py` / `probe_trace_retrieve.py` 的实测区域：

```text
[chain] start=0 -> [(0,'or'), (6,'and'), (10,'and')]
最终 BoolOpRegion op_chain = [(0,'and'), (6,'and'), (10,'and')]
merge_block = B5 (26-28)
IfRegion.condition_block = B3 (10-20)
```

#### 错误是如何产生的

1. `_detect_boolop_conditional_chain` 的成员极性只按 **末指令 opcode** 分类：
   - `core/cfg/region_analyzer.py:35110`：`op_type = 'and' if 'FALSE' in last.opname else 'or'`
   - `:35177`：`chain.append((current, op_type))`
2. B2 的末指令是 `POP_JUMP_FORWARD_IF_FALSE 172`，按上述规则被标成 `'and'`；但它的**假边目标是 172（then body）**，不是整条链的 merge 400。源码语义是 `not type` 的“真→body”，应属内层 `or` 组；产物把它当成外层 `and` 的第二个操作数，渲染成裸 `type`。
3. B1 的 `'or'` 被 `_normalize_none_check_op_types`（`core/cfg/region_analyzer.py:33284-33400`，只处理 NONE_CHECK_OPS）纠正为 `'and'`；B2/B3 是 IF_FALSE，不在该方法作用域。最终链变成三个 `'and'`，被 `_build_boolop_expression` 顺序压平为 `filename is None and type and type == 'file'`。
4. v161-NOTMIX 的专用探测 `_detect_fused_not_head_chain`（`core/cfg/region_analyzer.py:34137-34225`）确实存在，但它的入口条件要求 **`not` 组本身是链首**（`start_block` 末指令含 `FALSE`，且 head 目标 = and 子链末成员的 fall-through）。本例链首是 B1（`IF_NOT_NONE`），`not type or ...` 是第二个成员，因此该探测从未被调用（`probe_trace_retrieve.py` 只打印 `[chain] start=0 ...`，没有 `[fused_not_head]` 行）。
5. 结论：这是 **v161-NOTMIX 的非链首残形**：标准走查先成功，把嵌套的 `not A or (B and C)` 当成外层 and 成员吸收，极性融合探测没有机会介入。

#### 直接回答题干

- 守卫混合链的渲染与实际不符，**是的**：真实是 `A and (not B or C)`，产物是 `A and B and C`（实模块还额外产生了嵌套 if/else 与重复 `open`）。
- 错误行与字节码块的对应：
  - `request_now.py:1302` 的 `if filename is None and type:` ↔ B1/B2；
  - `request_now.py:1303-1306` 的嵌套 `if type == 'file': ... else: fp = self.open(...)` ↔ B2/B3 的假边目标被误当成外层 else/merge；
  - B2 的假边 172 是 then body，不是 merge 400。
- 最小复现 `mx2_b` 只保留守卫即失败，说明主因就是该混合链；双层 try/finally 是次因/放大因素，不是必要条件（`mx2_a` 与 `mx2_b` 同错）。

---

## 4. 同族 or 两族？

**结论：两族，不共享同一处修复代码。**

| 单元 | 族 | 具体位置 | 证据 |
|---|---|---|---|
| `ftp_open` | BoolOpRegion/for-iterable 归属族（与 v162-CHAINGRAFT 相邻，但不是同一处代码） | `core/cfg/region_ast_generator.py:8026-8032`（`_loop_generate_for` 的 `merge_block is for_iter_setup`）；镜像 `:53004-53010`（`_generate_boolop`） | B25=696-700 同时含 `STORE_FAST type` 与 `LOAD_FAST attrs; GET_ITER`；BoolOpRegion.merge_block 与 LoopRegion.for_iter_setup 同为 B25；iter_expr 直接取整条 BoolOp 链 |
| `retrieve` | v161-NOTMIX 残形 | `core/cfg/region_analyzer.py:35110/35177`（`_detect_boolop_conditional_chain` 按 opcode 标 'and'）；`:34137-34225`（NOTMIX 探测仅限链首）；`:33284-33400`（只纠 NONE_CHECK 首成员） | B2 假边→172 body，不是 merge 400；op_chain 最终 `[and,and,and]`；`_detect_fused_not_head_chain` 从未被调用 |

概念上两者都触及“BoolOpRegion 的块级边界”，但：

- `ftp_open` 的问题在 **消费端**（用 `merge_block` 身份把 BoolOp 当 iterable），链本身（`file and 'I' or 'D'`）是正确的；
- `retrieve` 的问题在 **检测端**（把 `not B or C` 的非首成员标成 and 并压平），链的 op_chain 本身就是错的。

因此不能用一个门同时修好；需要两个独立门控，分别回归验证。

---

## 5. 下一步修复建议（候选门控，I.4 白名单）

### 5.1 `ftp_open` 族

**门控位置**：`_loop_generate_for` 选中 `_boolop_for_iter` 之前（`region_ast_generator.py:8026-8032`），以及 `_generate_boolop` 的 for-iter 分支（`:53004-53010`）。

**候选条件（只读 CFG/块指令/末指令 opcode，不依赖名字/偏移常量）**：

> `merge_block` 必须真的是 `GET_ITER` 的迭代对象来源：`merge_block` 的有效指令以 `GET_ITER` 收尾，且在 BoolOp 值汇合之后、`GET_ITER` 之前**不存在 `STORE_*` / `POP_TOP` 等语句消费**。

对本例最直接的判别：

```python
# merge_block = 696-700，含 STORE_FAST type → 不是 iterable
if any(i.opname.startswith('STORE_') for i in merge_block.instructions):
    skip_boolop_for_iter = True
```

更一般地可限定为“`GET_ITER` 之前最后一个有效指令是 `LOAD_*`/`BUILD_*` 等值产生指令，而不是 `STORE_*`/`POP_TOP`”。这仍在 I.4 白名单：块内指令 opcode + 末指令 + 后继/CFG 关系，不引入名字白名单。

**命中后的行为**：

- 不设置 `_boolop_for_iter`，让 `iter_expr` 保持 `None`；
- 走 `_loop_extract_for_iter_pre_stmts`（`:12033`）把 B25 拆成：
  - pre_stmt：`type = file and 'I' or 'D'`（若尚未发射）；
  - iter_instrs：`LOAD_FAST attrs; GET_ITER` → `for attr in attrs`。
- 实模块中 TernaryRegion 已发射 `fw=...` 与 `type=...`，需用现有 `_fis_pre_stmts` + `_entry_prefix_emitted_blocks` 守卫（`:8183-8186`）避免重复发射；最小复现 `mx1_a` 则应由该路径补回赋值行。
- `_generate_boolop` 的镜像分支也要用同一门，避免生成顺序变化时又从另一条路把 BoolOp 当 iterable。

**验证用例**：

- 正例保持：`for x in (a or b):`、`for x in (a and b):`（BoolOp 本身就是 iterable，merge 块应为 `GET_ITER` 收尾且无 STORE）。
- 新修：`mx1_a`~`mx1_e`、真实 `ftp_open`。
- 回归：含前置语句的 for-iter（`total = 0; for x in (a or b):`）、`for x in (a if c else b):`（TernaryRegion 路径，不应被本门影响）。

### 5.2 `retrieve` 族

**门控位置**：`_detect_boolop_conditional_chain` 的成员追加处（`region_analyzer.py:35110/35177`），或 `_create_boolop_region_from_chain` 的链验收处（`:33709` 起）。

**候选条件**：

> 一个 `IF_FALSE`/`IF_TRUE` 成员只有在它的**短路边目标等于整条链的共享出口**时，才能按 `'and'` 追加；若假边目标落在 then body（非共享出口），该成员属于嵌套的 `not ... or ...` 组，应截断外层链，交给 IfRegion 嵌套重建（或交给扩展后的 NOTMIX 探测）。

对本例：

- B1 假/非 None 目标 = 26（外层 merge）→ 可作外层 and 成员；
- B2 假目标 = 22（then body）≠ 26 → 停止外层链；B2/B3 由内层 IfRegion/BoolOp 重建为 `if not type or type == 'file':`，控制流等价。
- 若希望保持单层文本形态，可把 NOTMIX 探测从“仅链首”扩展到“链内任意成员”：当某成员 `M` 的假目标 `X` ≠ 外层 exit、且 `M` 的 fall-through 继续到下一条件、下一条件的假目标 = 外层 exit 时，构造内层 `BoolOp(or, [not <M expr>, <next expr>])`，再嵌入外层 and。但该扩展风险更高，建议先走“截断 + 嵌套 IfRegion”路径，判官只看控制流。

**必须保留的既有形态**：

- `not A or (B and C)` 链首（v161-NOTMIX 已修）——`_detect_fused_not_head_chain` 的入口条件不能放宽到误吞 NOTTAIL；
- `A and not (B and C)`（v148-NOTTAIL）——与 NOTMIX 在首续接门完全镜像，任何按“假边目标 ≠ merge”截断的判据都要在 NOTTAIL 上验证；
- 双成员 `not A or B`——NOTMIX 明确不命中，应继续走原 HEAD 路径；
- `A and (B or C)`（无 not）——`mx2_d` 已正确，门控不能把它截断成嵌套 if 而改变文本/字节码形态（虽然控制流等价，仍建议保持原路径）。

**风险族清单**：

| 族/路径 | 风险 |
|---|---|
| v161-NOTMIX | 本次正是其非链首残形；修改链接受/截断会直接影响 `not A or (B and C)` 的链首命中与双成员排除 |
| v148-NOTTAIL | 与 NOTMIX 共享“假边/真边对调”的局部同形，NOTTAIL 的 `A and not (B and C)` 依赖现有 B116 豁免；截断门可能使其退化为嵌套 if |
| v162-CHAINGRAFT | 虽不是同一处代码，但 IfRegion 的 merge/else 归属与链截断耦合；改 `_detect_boolop_conditional_chain` 后需跑 if/elif 链尾（continue）回归 |
| for-iter Ternary / while BoolOp | `ftp_open` 门控在 LoopRegion 生成入口，可能影响 `for x in (三元)`、`while` 条件链；用 `_loop_extract_for_iter_pre_stmts` 的既有 pre_stmt 通道做对照 |
| `_normalize_none_check_op_types` | 它已负责把 B1 的 `'or'` 纠成 `'and'`；若在检测阶段提前截断，需确认 NONE_CHECK 首成员仍能被正确归类 |

---

## 6. 复现/探针文件与命令

| 文件 | 用途 |
|---|---|
| `request_now.py` | 当前整模块反编译产物（87,861 bytes） |
| `ftp_open.dis` / `retrieve.dis` | 两函数的 `dis` 反汇编（含异常表） |
| `extract.py` | 按函数名切片打印源码/产物函数体（不整读大文件） |
| `probe_regions.py` | 建 CFG + RegionAnalyzer，打印块布局、BoolOp/Loop/If 区域及 merge/for_iter_setup |
| `probe_claim.py` | 追踪 `_loop_generate_for` 是否用 BoolOpRegion 作 iterable |
| `probe_trace_retrieve.py` | 追踪 `_detect_boolop_conditional_chain` / `_detect_fused_not_head_chain` 的实际调用 |
| `probe_emit.py` / `probe_emit2.py` | 追踪 `type = ...` 由哪条语句/区域路径发射 |
| `judge_log.txt` | 全部最小复现的判官输出 |
| `mx1_*` / `mx2_*` | 最小复现的 `_src.py` / `.pyc` / `_out.py` |

关键命令：

```powershell
D:/Python/python.exe -I -X utf8 pycdc.py D:/Python/Lib/urllib/__pycache__/request.cpython-311.pyc -o D:\temp\opencode\cl_layout\r163\request_now.py
D:/Python/python.exe -I -X utf8 scripts/pyc_verify.py single D:\temp\opencode\cl_layout\r163\mx1_a.pyc --source D:\temp\opencode\cl_layout\r163\mx1_a_out.py
D:/Python/python.exe -I -X utf8 scripts/pyc_verify.py single D:\temp\opencode\cl_layout\r163\mx2_b.pyc --source D:\temp\opencode\cl_layout\r163\mx2_b_out.py
```

探针运行时设置 `PYTHONDONTWRITEBYTECODE=1`，只 import 仓库模块，不改仓库文件；`git status -- core scripts pycdc.py bytecode parsers utils` 为空。

---

## 7. 一句话总结

- `ftp_open`：`type = file and 'I' or 'D'` 的 BoolOpRegion merge 块 B25（696-700）同时含 for 的 `STORE_FAST`/`LOAD attrs`/`GET_ITER`，`_loop_generate_for` 仅凭 `merge_block is for_iter_setup` 就把整条链当 iterable，真正的 `attrs` 被越过；**for-iterable 提取在基本块粒度越界**。
- `retrieve`：B2 `type` 的假边目标是 then body(172) 而非 merge(400)，`_detect_boolop_conditional_chain` 只按 opcode 把它标成 `'and'`，`A and (not B or C)` 被压平成 `A and B and C`；v161-NOTMIX 探测只认链首，未覆盖该非首成员；**NOTMIX 残形**。
- 两族不共享修复代码：前者改 `region_ast_generator` 的 for-iter BoolOp 门，后者改 `region_analyzer` 的条件链极性/目标验收；分别回归 NOTMIX/NOTTAIL 与 for-iter Ternary/CHAINGRAFT。
