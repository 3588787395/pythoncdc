# Round 02 — 修复报告（修复工程师）

- 环境：`D:/Python/python.exe`（3.11.7），pyc 魔数 `a70d0d0a`
- 判据：`minimal_repros/run_repros.py`（`compile(src) → decompile(src) → compile(out) → 递归比对 co_code/co_names/co_varnames`）
- 基线：`PASS 0 / FAIL 13`（对照组 4/4）
- 本轮结果：**`PASS 9 / FAIL 4`**（对照组 4/4）
- 未修改任何 `OK.py`、未修改 `run_repros.py`、未修改 `testqouter/round1/base.py`

| Family | 优先级 | 复现 | 修复前 | 修复后 |
|---|---|---|---|---|
| **F4** assert 前赋值被丢弃（语义错误） | **P0** | 05 / 06 / 07 | 0/3 | **3/3 PASS** |
| **F5** with/if 之后的 bare return 丢失 | P0/P1 | 08 / 09 | 0/2 | **2/2 PASS** |
| **F3** 连续 `obj.attr = a or b.c` 截断 | P1 | 03 / 04 | 0/2 | **2/2 PASS** |
| **F1** `<call>().attr = value` 值丢失 | P2 | 01 | 0/1 | **1/1 PASS** |
| **F8** if 块内 import 退化 | P4 | 12 / 13 | 0/2 | **1/2 PASS**（12 通过，13 仍 FAIL） |
| F2 / F6 / F7 | P3/P4 | 02 / 10 / 11 | 0/3 | 0/3（未修） |

---

## 1. F4 — assert 之前紧邻的赋值语句被丢弃，变量退化为 `LOAD_GLOBAL`

**现象**（`repro_05.py`）

```python
def fill(self, trade):
    amount = trade.amount        # ← 整条消失
    assert self.filled_amount + amount <= self.amount
```

反编译产物里 `amount` 变成 `LOAD_GLOBAL amount` —— 局部变量变全局查找，**语义错误**而非形状差异。

**根因 → 定位**

- `core/cfg/region_ast_generator.py:2796` `_generate_assert` 的 `cond_instrs` 扫描循环，
  `STORE_FAST/STORE_NAME/STORE_GLOBAL/STORE_DEREF` 分支里的 `cond_instrs = []`（原 2833 行附近）。
- 该重置的意图是「防止条件表达式吸收前缀赋值」，局部正确；但被重置掉的指令**没有任何一方发射**，
  语句直接消失。

**修复方案的算法依据（4 原则）**

- **原则 3（嵌套即抽象节点）**：`AssertRegion` 只暴露一个 `ast.Assert` 抽象节点，不得吞并同块内
  不属于它的语句。旧代码满足「条件表达式不含前缀指令」，却违反了原则 3 的下半句。
- **原则 1（自底向上归约）**：前导段是块内更低层的结构（完整语句），先于 assert 条件表达式归约。
- **原则 4（入口引用语义）**：父序列通过 `condition_block` 引用 `AssertRegion`；前导语句位于入口
  块内、区域之外，由父序列就地发射，位置在 `ast.Assert` 之前（保序）。
- **原则 2（每块唯一归属）**：块仍整体归属 `AssertRegion`，只是区域内部再按「语句 / 条件表达式」
  两个抽象层次展开；发射后登记 `_assert_prefix_emitted_blocks`，父序列通用扫描据此跳过。

**结构性判据（新增，非模式匹配）**

基本块的定义是「极大直线指令序列，控制流只在块末转移」。若块末是条件跳转，该块承载两段内容：

- 前导段：若干条**已完结**的语句 —— 语句的栈不变式是「执行完毕后值栈回到块入口深度 0」
  （简单赋值 / 属性赋值 / 下标赋值 / 增强赋值 / 表达式语句 / import / raise / del 全部满足，
  与具体语法形式无关）；
- 条件段：从某条指令起把值栈从 0 抬升到 1，并由块末条件跳转消费。

故「条件表达式起点」= **前向栈深模拟中，块末跳转之前最后一次回到深度 0 的位置之后**。
这纯依赖 CPython 的 stack effect（`dis.stack_effect`），不依赖任何 opcode 组合的模式表，
且「取最后一次归零点」天然覆盖前导段有多条语句的情形。反向回溯与前向等价，但前向单趟即可。

**改动位置**

| 文件 | 位置 | 内容 |
|---|---|---|
| `core/cfg/region_ast_generator.py` | `import dis`（第 15 行） | 新增，供 `dis.stack_effect` 使用 |
| 同上 | `_split_block_condition_prefix`（161） | 新增：按栈纪律切分条件块的前导语句段 |
| 同上 | `_instruction_stack_effect`（224） | 新增：取指令栈效应；不可得返回 None（保守） |
| 同上 | `_collect_assert_prefix_stmts`（240） / `_take_assert_prefix_stmts`（260） | 新增：前导段归约为语句并暂存 / 取出 |
| 同上 | `_generate_assert`（2796） | 扫描前调用 `_collect_assert_prefix_stmts` |
| 同上 | 6 个调用点（527 / 6299 / 9181 / 9194 / 17207 / 17509） | `body_stmts.extend(self._take_assert_prefix_stmts(r))`，置于 Assert 之前 |
| `core/cfg/region_analyzer.py` | `_identify_assert_regions` docstring（12560） | 补「入口块的直线段分解（栈纪律判据）」、Step 8、「已知失败模式 / 本轮修复 F4」 |

**保守性**：任一指令 stack effect 不可得、或模拟中栈下溢 → 返回空列表，退化为切分前行为。

**涉及复现**：`repro_05.py` / `repro_06.py` / `repro_07.py`（3/3 PASS）

---

## 2. F5 — `with` / `if` 之后的 bare `return` 丢失

**现象**（`repro_08.py`）：`with open(...) as fh: ...` 之后的 `return` 被丢弃，编译后
`JUMP_FORWARD to 132`（越过内联 handler）变成直接的 `LOAD_CONST None; RETURN_VALUE`。

**根因 → 定位（两处叠加）**

1. `core/cfg/region_analyzer.py:9832` `_collect_normal_exit_cleanup` 以「块内无用户代码」这一
   **形态**判据收集清理块；其 `RETURN_VALUE` 守卫还显式放行了 `LOAD_CONST None; RETURN_VALUE`。
   于是恰好形如隐式 return 的 **with 出口块**被误收进 `cleanup_blocks`，`WithRegion` 越界吞掉
   with 之后的那条语句并标记为 generated。
2. 即使区域划分修正、`Return` 节点进入 AST，`code_generator._filter_trailing_return_none`
   仍按「函数末尾 return None 即隐式返回」把它过滤掉 —— 对普通函数成立，但当 with 是倒数第二条
   语句时 CPython 必须生成越过 handler 的 `JUMP_FORWARD`，删掉 return 会连这条跳转一起消失。

**结构性判据（新增，非模式匹配）**

实测三种布局（用 `D:/Python/python.exe` + `dis` 验证）：

| 源码 | `__exit__` 块结尾 | handler 位置 |
|---|---|---|
| with 是最后一条语句 | `POP_TOP`，**fall-through** 进隐式 return | 排在 return **之后** |
| with 之后有 `return` | **`JUMP_FORWARD → X`** | 夹在 `__exit__` 与 X **之间** |
| with 之后有普通语句 | **`JUMP_FORWARD → X`** | 夹在 `__exit__` 与 X **之间** |

即：**「出口块由无条件转移到达」⇔「该块是 with 之后的真实源码」**。这只看控制流边的性质
（无条件转移 vs 顺序 fall-through）与异常表给出的 `body_end`，**不看块内是否形如隐式 return**
—— 正是旧形态判据失效的地方。`_find_with_exit_block` 从「含 `body_end` 偏移的块」（= normal-exit
`__exit__` 块）出发取唯一转移目标即得出口块。

**算法依据（4 原则）**

- **原则 3 + 4**：`WithRegion` 是**单入口（BEFORE_WITH 块）单出口（出口块）**区域，只归约 `with`
  语句本身；出口块由父序列通过控制流「出口引用」取得并生成。区域以 `exit_block` / `exit_via_jump`
  两个字段**引用**它，不改变归属（**原则 2**）。
- 生成端：出口块产生的 `return None` 打 `_explicit_return` 指令背书（本项目既有通道，
  `ast_converter` 保留、`code_generator` 据此不过滤），而非新增后处理。

**改动位置**

| 文件 | 位置 | 内容 |
|---|---|---|
| `core/cfg/region_analyzer.py` | `WithRegion`（847–848） | 新增字段 `exit_block` / `exit_via_jump` |
| 同上 | `_find_with_exit_block`（9944） | 新增：定位 with 出口块与到达方式 |
| 同上 | `_build_single_with_region`（10013，原 9992 附近） | 出口块从 `cleanup_blocks` 剔除 + 写入两个字段 |
| 同上 | `_identify_with_regions` docstring（10122） | 补「出口块的控制流判据」、Step 5、「已知失败模式 / 本轮修复 F5」 |
| `core/cfg/region_ast_generator.py` | `_with_jump_exit_blocks`（35771） | 新增：所有「无条件跳转到达的 with 出口块」集合（带缓存） |
| 同上 | `_mark_with_exit_return_explicit`（35845） | 新增：给出口块产生的 return None 打指令背书 |
| 同上 | `_generate_block_statements`（35873） + `_generate_block_statements_body`（35886） | 薄包装：单一漏斗施加上述标记，判据只有一份 |

**保守性**：`normal-exit` 块定位失败、转移目标不唯一、或出口块已被非 WithRegion 区域认领 →
放弃剔除（`region_exit_block = None`），退化为剔除前行为。

**涉及复现**：`repro_08.py` / `repro_09.py`（2/2 PASS）

---

## 3. F3 — 连续 `obj.attr = a or b.c`：第 2 条起被截断为裸表达式，其后语句全丢

**现象**（`repro_04.py`）

```python
def f(o, a, b, env):
    o.x = a or env.a
    o.y = b or env.b     # ← 退化成裸表达式 `b`
    return o             # ← 变成 `return env.b`，后续全丢
```

**根因 → 定位**

`repro_04` 的 CFG（偏移）：块 0（`a` + `JUMP_IF_TRUE_OR_POP→18`）、块 6（`env.a`）、
块 18（`LOAD o; STORE_ATTR x; LOAD b; JUMP_IF_TRUE_OR_POP→46`）、块 34（`env.b`）、
块 46（`LOAD o; STORE_ATTR y; LOAD o; RETURN_VALUE`）。

- `BoolOpRegion#1 entry=0 blocks=[0,6,18]`，`BoolOpRegion#2 entry=18 blocks=[18,34,46]`；
- **`block_to_region[18]` 只记了 #1** —— #2 对 `get_region_for_block` 不可见，永远等不到派发；
- #1 的 R78 分支（STORE_ATTR 之后的剩余指令）退化成通用块语句生成，把 `LOAD b` 输出成裸表达式 `b`。

**修复方案的算法依据（4 原则）**

这不是「归属冲突」，而是**归属粒度**问题。原则 2 的正确读法是「每个块在任何**层级**只归属一个
区域」——同一个块可以按指令区间在不同**层级**分别归属。识别阶段不做指令级切分（保持块粒度，
避免牵动全部区域识别），改在生成阶段由上游区域归约完成处显式移交：

- **原则 3**：上游 `BoolOpRegion` 的归约在 `merge_block` 的 `STORE_ATTR` 处结束；
- **原则 4**：其后剩余指令若属于某个以该块为 entry 的下游区域，父序列通过 entry 引用该区域
  （`_generate_region`）而非就地生成裸语句。

**结构性判据**：下游区域必须 **向本块之外延伸**（`set(r.blocks) - {block}` 非空）。这是必要的：
analyzer 会为未归约块建只含该块一个块的**退化容器 Region**（本例中 `Region entry=46 blocks=[46]`），
若派发给它，等价于走通用块语句路径，会掩盖真正的下游区域并吞掉剩余语句（实测会丢掉 `return o`）。
判据只依赖区域的 entry 指针、blocks 集合与生成状态，不依赖任何 opcode 形态。

**改动位置**

| 文件 | 位置 | 内容 |
|---|---|---|
| `core/cfg/region_ast_generator.py` | `_downstream_region_entry`（35801） | 新增：查找「以 block 为 entry、向该块之外延伸、未生成」的区域 |
| 同上 | `_generate_boolop` R78 分支（27216–27228） | 剩余指令先查下游区域，命中则派发 `_generate_region`；否则保持原通用路径 |
| 同上 | `_generate_boolop` docstring（26861） | 补「已知失败模式 / 本轮修复 F3」 |
| `core/cfg/region_analyzer.py` | `_identify_boolop_regions` docstring（18905） | 补「块的指令级分区（一个块可横跨两条语句）」+「已知失败模式 / 本轮修复 F3」 |

**涉及复现**：`repro_03.py` / `repro_04.py`（2/2 PASS）

---

## 4. F1 — `<call>().attr = value`：STORE_ATTR 的值丢失成 `None`

**现象**：`f().x = 5` → `f().x = None`（`LOAD_CONST 5` 变 `LOAD_CONST None`）。

**根因 → 定位**

`core/cfg/region_ast_generator.py:41123` `_build_attr_assign` 的**对象链扫描**：从 `STORE_ATTR`
向前扫 `LOAD_ATTR*`，再吃一个 `LOAD_FAST/NAME/GLOBAL/DEREF`，遇到任何其他指令即 `break`。
对象端自身是 `CALL` 时扫描立即终止 → `_obj_chain_instrs` 为空 → 触发「回退到完整 obj_instrs」
分支，把「值 5 + 对象 `f()`」整段当成对象、值段为空 → `value = Constant(None)`。
该假设（`对象端 = LOAD_* + LOAD_ATTR*`）对 `a.x = v` / `a.b.c = v` 成立，对一切「对象端是复合
表达式」都不成立。

**结构性判据（替代形态假设）**

CPython 3.11 定义 `STORE_ATTR(namei)` 为 **`TOS.name = TOS1`**：栈顶 TOS 是**对象**，次栈顶 TOS1
是**值**；源码侧编译器也恒为「先压值、后压对象」（`self.x = f()` 先求 `f()` 再压 `self`）。
因此在紧邻 `STORE_ATTR` 之前的指令序列上跑一遍表达式重建器，其**残留值栈的最后两项**就是
`(TOS1=值, TOS=对象)`。这纯依赖 CPython 的指令栈语义与重建器自身的栈模拟，对属性链 / 调用 /
下标 / 运算 / 任意复合表达式一视同仁。

**改动位置**

| 文件 | 位置 | 内容 |
|---|---|---|
| `core/cfg/region_ast_generator.py` | `_build_attr_assign`（41123，栈切分在 41295 附近） | 新增 Step 3：用重建器残留值栈做 TOS/TOS1 切分；不适用时回退旧对象链扫描 |
| 同上 | `_build_attr_assign` docstring | 新增（该方法原本无 docstring）：算法依据 / 归约过程 / 已知失败模式 |

**归属说明**：属性赋值**不是区域类型**（无 `RegionType`、无 `_identify_*_regions`），它是最低层的
**语句级表达式归约**（原则 1 中比区域更低一层），由区域生成方法遍历块内指令时调用。按项目规范
把反编译逻辑写在该方法 docstring，并在此交叉引用。

**保守性**：栈深 < 2，或栈顶已归约为语句节点（`Assign`/`Return`/`Import` 等，说明 `obj_instrs`
里混入了前序语句）→ 退回旧路径。

**涉及复现**：`repro_01.py`（PASS）

---

## 5. F8（部分）— if 块内的 `import x` 退化

**现象**：`import ptvsd` → `ptvsd = None`（并且重复一次），末尾多出 `return None`。

**根因 → 定位（两处叠加，都在 `_generate_boolop` 的 `pre_stmts` 链路上）**

1. `core/cfg/region_ast_generator.py:40065` `_build_prefix_stmt_list` 按「见到 `STORE_*` 就把 buf
   里累积的指令当成一个赋值右值」切分。CPython 3.11 的 `import ptvsd` 是
   `LOAD_CONST level + LOAD_CONST fromlist + IMPORT_NAME + STORE_*` —— **归约入口是 `IMPORT_NAME`
   而不是 `STORE_*`**；`IMPORT_NAME` 不被表达式重建器识别，buf 里只剩两个 `LOAD_CONST` →
   `ptvsd = None`。
2. `_generate_boolop` 的三处 `return pre_stmts + results if pre_stmts else results` 把 `pre_stmts`
   **重复前置** —— `results` 在 `results = list(pre_stmts)` 处已含 `pre_stmts`，非空时该 return
   必然产出两份前导语句（报告中「重复一次」即此）。

**修复的算法依据**

- 「按归约入口切分」= **原则 1（自底向上归约）**：一条语句的归约入口是它最内层的消费指令
  （普通赋值是 `STORE_*`，import 是 `IMPORT_NAME`）。含 `IMPORT_NAME/IMPORT_FROM` 时委托既有的
  `_build_statements_from_instructions`（内置 import 状态机，覆盖 import / import-as /
  from-import / from-import-as / from-import-multi），不新增第二份实现。
- 重复前置是**每块唯一归属**的破坏（同一段指令产生两个 AST 节点），直接 `return results` 修正。

**改动位置**

| 文件 | 位置 | 内容 |
|---|---|---|
| `core/cfg/region_ast_generator.py` | `_build_prefix_stmt_list`（40065） | 含 import 时委托 `_build_statements_from_instructions` + docstring 补已知失败模式 |
| 同上 | `_generate_boolop` 三处 return（原 27198 / 27240 / 27269） | `pre_stmts + results` → `results` |
| 同上 | `_generate_boolop` docstring（26861） | 补「已知失败模式 / 本轮修复 F8」 |

**涉及复现**：`repro_12.py`（PASS）。
`repro_13.py`（真实 115→18 大函数）**仍 FAIL** —— 修复后 import 已正确还原、重复已消除，剩余差异是
语句重排：结尾的 `engine.config.other.enable_debug = config.timeout or 10` 被提到 if 体最前，
其后插入 `return None`，使 import 与嵌套 if 变成不可达代码。定位在
`_if_generate_then_branch` 的 `then_stmts = _expr_child_stmts + then_stmts`（无条件前置子区域语句，
未按块偏移排序）+ boolop merge_block 尾部的隐式 return 被当作语句发射。**本轮未修**（该处改动
影响面覆盖全部 if-then 生成，需要独立的回归预算）。

---

## 6. 反模式自检

新增方法名全部列出（无一个命中禁用前缀）：

```
region_analyzer.py
  _find_with_exit_block                    (9944)
region_ast_generator.py
  _split_block_condition_prefix            (161)
  _instruction_stack_effect                (224)
  _collect_assert_prefix_stmts             (240)
  _take_assert_prefix_stmts                (260)
  _with_jump_exit_blocks                   (35771)
  _downstream_region_entry                 (35801)
  _mark_with_exit_return_explicit          (35845)
  _generate_block_statements_body          (35886)   ← 原方法重命名，非新增语义
```

| 检查项 | 结果 |
|---|---|
| 新增 `_fix_` / `_merge_` / `_patch_` / `_fallback_` / `_hack_` / `_workaround_` / `_temp_` 前缀 | **0**（`git diff -U0 \| grep -cE '^\+.*(_fix_\|_merge_\|_patch_\|_fallback_\|_hack_\|_workaround_\|_temp_)'` = 0） |
| 新增 `depth > N` 之类硬编码层数 | 0 |
| 为单个语料文件打特判 | 0（全部判据基于 CFG 性质 / 栈纪律 / 区域结构，语料无关） |
| 跨区域跨层次的启发式规则 | 0（新判据：栈纪律、控制流边性质、区域 entry/blocks 结构） |
| 破坏嵌套天然支持的后处理 | 0（F5 走既有 `_explicit_return` 通道；F3 是生成期派发而非事后合并） |

> 说明：`git diff` 的统计里包含**本轮开始之前工作树中已存在的、未提交的改动**（`git status` 初始即
> 显示 `core/cfg/region_analyzer.py` 与 `core/cfg/region_ast_generator.py` 为 modified）。上表与方法
> 清单只统计本次修复新增的内容。

---

## 7. 验证结果

### 7.1 `run_repros.py`（判定口径未修改）

```
[PASS] repro_01.py      F1
[FAIL] repro_02.py      F2   DataProxy 指令#5 ...
[PASS] repro_03.py      F3
[PASS] repro_04.py      F3
[PASS] repro_05.py      F4
[PASS] repro_06.py      F4
[PASS] repro_07.py      F4
[PASS] repro_08.py      F5
[PASS] repro_09.py      F5
[FAIL] repro_10.py      F6   f 指令#10 ...
[FAIL] repro_11.py      F7   __init__ 指令#4 ...
[PASS] repro_12.py      F8
[FAIL] repro_13.py      F8   setup 指令#5 ...
------------------------------------------------
复现用例 总计 13   PASS 9   FAIL 4
对照组 PASS 4/4
```

**PASS 0/FAIL 13 → PASS 9/FAIL 4**；对照组全程 4/4（比对器未放宽、未过严）。

### 7.2 有界回归（对照法，`repair_engineer/roundtrip_suite.py`）

为避免「只跑 13 个复现」的盲区，另外构造了标准库往返回归样本集，用
「修改前（`git stash`）/ 修改后」差分衡量。样本挑选确定性（`sorted(rglob)`），
只统计 PASS/FAIL，不改任何判据。

| 样本集 | 文件数 | 修改前 PASS | 修改后 PASS | 回归（PASS→FAIL） | 改善（FAIL→PASS） |
|---|---|---|---|---|---|
| 通用（3–80 KB） | 60 | 5 | **6** | **0** | `asyncio\transports.py` |
| 含 `with ` | 45 | 4 | **5** | **0** | `asyncio\transports.py` |
| 含 ` or ` | 45 | 3 | **4** | **0** | `asyncio\transports.py` |
| 含 `.x = ` | 44 | 2 | **2** | **0** | — |
| 含缩进 `import ` | 40 | 0 | **1** | **0** | `cProfile.py` |

合计 **234 个文件样本，0 回归，2 个改善**（`asyncio/transports.py` 在 3 个样本集中重复计数，
实际唯一改善文件为 `asyncio/transports.py` 与 `cProfile.py`）。

原始数据：`repair_engineer/{before_all.json, after_f8.json, before_all_with.json, after_f5_with.json,
before_f3_bool.json, after_f8_or.json, before_f1_attr.json, after_f1_attr.json,
before_f8_imp.json, after_f8_imp.json}`。

### 7.3 项目自带 `run_tests.py`

```
te04tryfinally: PASS
te027:          FAIL
```

`te027` 的 FAIL 经 `git stash` 对照确认是**基线既有问题**（修改前后一致），非本轮引入。

---

## 8. 本次改动**没有**做回归验证的部分（需另行执行）

1. **102 个 partial pyc 的全量批量回归** —— 按任务要求未执行。上表 234 个标准库文件样本是替代信号，
   但语料分布与 `site-packages` 不同（无量化交易业务代码、无 3.11 特有的大函数形状），
   **不能替代** 102 文件回归。
2. **`site-packages/**/*OK.py` 的比对** —— 未跑（`pyc_diff.py` / `testqouter/round1/base.py` 均未被调用）。
3. **`tests/` 下的完整套件** —— 只跑了 `run_tests.py`；`tests/run_all_tests.py`、
   `tests/control_flow_matrix/`、`tests/exhaustive/`、`tests/completeness/` 等未执行。
4. **F5 改动的 `code_generator` 侧影响面** —— F5 给出口块的 `return None` 打了 `_explicit_return`，
   该标记会让 `code_generator._filter_trailing_return_none` 与 `_generate_function_def_dict`
   不再过滤它。已用「含 `with ` 45 文件」样本验证 0 回归，但**未覆盖** `with` 嵌套 `try/finally`、
   `with` 在循环内、`async with` 等组合，建议补测。
5. **`_generate_block_statements` 的包装层** —— 该方法有 80+ 调用点（含递归），包装层会在递归路径上
   重复调用 `_mark_with_exit_return_explicit`。该函数幂等且只在「块是 with 出口块」时动作，
   但**未对递归深度/性能做压测**。
6. **F3 的 `_downstream_region_entry`** —— 只在 `_generate_boolop` 的 R78 分支接入。
   同一「块横跨两条语句」的形状在 `TernaryRegion` / `IfRegion` / `LoopRegion` 的类似分支上
   同样可能存在，本轮**未推广**，需要时另开一轮。
7. **F8 剩余部分（`repro_13`）** —— 未修，见第 5 节末。
8. **F2 / F6 / F7** —— 未修，未定位。

---

## 9. 下一步建议（按性价比）

1. **F7（repro_11）**：`STORE_ATTR` 的值为三元时整条语句及后续全部丢失。根因形态与 F3/F4 同源
   ——「三元汇合点 + 后续语句同块」，可复用本轮新增的 `_downstream_region_entry` /
   `_split_block_condition_prefix` 两个结构性工具，边际成本低。签名 `LOAD_FAST → LOAD_FAST`
   在 102 文件中命中 14 个。
2. **F8 剩余（`repro_13`）**：修 `_if_generate_then_branch` 的 `then_stmts = _expr_child_stmts +
   then_stmts`（按块偏移插入而非无条件前置）+ boolop merge_block 尾部隐式 return 的抑制。
   修好可翻转 `plugin_system_debug/__init__.pyc`（115→18，本批单函数损失最大）。
3. **F2 / F6**：各 1 文件，需独立定位。

---

## 10. 交付物

```
rounds/round_02/repair_engineer/
├── fix_report.md                 本文件
├── probe.py                      单文件探针（源码/反编译产物/指令级差异）
├── trace_assert.py               追踪 _generate_assert 调用来源与区域识别结果
├── trace_roles.py                打印块角色 / 所属 region / 指令
├── trace_with.py                 追踪 _generate_with 与函数体语句序列
├── roundtrip_suite.py            有界往返回归套件（支持 must_contain 过滤）
├── exp_stack.py                  dis.stack_effect 栈深模拟实验（F4 判据验证）
└── *.json                        回归样本原始结果（用于差分）
```
