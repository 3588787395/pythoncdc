# rr-v5r177 — subprocess SP3 STMT-DROP 收口（Popen.__del__）

> 仓库 `F:\Downloads\pythoncdc-main`；解释器 `D:/Python/python.exe -I -X utf8`；cwd=仓库根。
> 单文件单 anchor：`core/cfg/code_generator.py`（+53/−3）。零其他源文件写入（`core/ast_nodes.py`、
> `core/cfg/ast_converter.py` 的 `git status M` 是 CRLF/stat 噪声，`git hash-object` == HEAD，`git diff` 为空）。

## 1. 缺陷复验（recon 定性成立）

复现：`D:\temp\opencode\cl_layout\r170recon\repro\real\sp_Popen___del___real.py`（逐字抽取自 3.11
`subprocess.py` `Popen.__del__`），改前判官 `failure 2/3`、`Popen.__del__` = **Different control flow**：

- 原始 41 条指令 / CFG 11 节点 14 边；产物 27 条 / 7 节点 8 边（`work/diff_del.txt`）。
- 首个差异 idx=25：原 `50 LOAD_FAST self` → 产物 `50 LOAD_CONST None`；
  opname edit script 删除 `orig[25:35]`（`LOAD_FAST/LOAD_ATTR/POP_JUMP_FORWARD_IF_NOT_NONE/
  LOAD_GLOBAL/POP_JUMP_FORWARD_IF_NONE/LOAD_GLOBAL/LOAD_METHOD/LOAD_FAST/CALL/POP_TOP`）
  与 `orig[37:41]`（两个隐式 return None 块）。
- 即：**整条 `if self.returncode is None and _active is not None: _active.append(self)` 蒸发**，
  不是形态差异。

## 2. 根因（函数:行号）

产物 AST 里尾部条件**并未丢失**：`_boolop_chain_exits_are_distinct_sinks`（两个互不相同的
隐式 `return None` sink 出口）正确拒绝把该链折叠成 BoolOp，链成员由 IfRegion 逐层认领，转换后
AST 为 `If(self.returncode is None) → If(_active is not None) → _active.append(self)`。

丢失发生在生成端：
`core/cfg/code_generator.py` `CodeGenerator._generate_if`（L1539-1550）→
`_filter_duplicate_if_in_else`（L1644-1696）只按**条件文本**判「elif 重影」。该尾部 if 的条件文本
与同一 orelse 里前一条独立语句 `if self.returncode is None: _warn(...)` 相同（条件撞车），
于是被当成结构化分析重影删除，并就地改写 `node.orelse._nodes` 使其永久消失。

## 3. 修复谓词

「elif 重影」判据由「条件文本相同」升级为「**整臂签名相同**」= 条件文本 + then 体渲染文本 +
else 体渲染文本（新 helper `_if_arm_signature`，L1717；`Optional[str]`，异常返回 None）。
结构化分析重影由同一组块二次发射，整臂一致；仅条件撞车的独立语句 body 不同，必须保留。
签名不可得时回退旧行为（按条件去重），既有重影清理路径逐位不变（C3）。

## 4. 验收读数

### 4.1 subprocess `Popen.__del__` 判官

- 现树整模块重解，判官逐单元：`<module>.Popen.__del__: Success: Equal`
  （`bc_a`/`bc_b` 均 41 instructions；`r177verify/unit_del_judge.py`）。
- 子进程失败名单 **5 → 4**：
  - r176（5）：`__init__` / `__exit__` / `__del__` / `_internal_poll` / `_wait`
  - r177（4）：`__init__` / `__exit__` / `_internal_poll` / `_wait`（不含 `__del__`）
- subprocess **73/78 → 74/78**。
- 产物全文件 diff 仅 1 hunk：恢复 3 行（`if self.returncode is None:` /
  `if _active is not None:` / `_active.append(self)`），bytes 69910→70034，sha16
  `45a98b3fdf2a94b8`→`9ab5e6bfdca7cc98`。`call`/`run`/`_execute_child`/`_check_timeout`/
  `list2cmdline`/`_on_error_fd_closer` 逐单元 BYTE-SAME。

### 4.2 四语料

| 语料 | r177 | 与 r176 产物 |
|---|---|---|
| request | **194/194** | BYTE-SAME (`db2172e8f1a69af6`) |
| difflib | **62/62** | BYTE-SAME (`d70df6006a50f33f`) |
| tarfile | **156/160** | BYTE-SAME (`fcb8a7fbb7b246b2`) |
| cookiejar | **101/105** | BYTE-SAME (`9c793bf9f0474ba1`) |

除 subprocess 外零文本变化；文本变化处就是上面唯一 hunk，且与源码第 13–15 行逐字对应。

### 4.3 458 电池（硬门）

`battery177.py`（复制 `fresh/tarfile167/r170_regress.py`，仅改 TMP/OUTDIR/EV，先删 scratch）：

- **TEXT-DIFF = 17 / 458**，与允许集**逐案相同**（mk_iterencode/yp2/te_variants8/fdt/pc12/pc9/pm1、
  v111_m1_exact/v111_m2_no_genexpr/v111_two_if_diffmsg、E3_andnot_nochainstmt、E161 六案），
  **17/17 全 BYTE-EQUAL**；无非允许新增。
- `C7_skipedge` **TEXT-SAME**（签名 DIFF 为 r110 起的既有登记）。
- `R110 案: 169 / TEXT 状态一致 161 / 签名一致 167`（= r176/r175）。
- `REG-10: CHANGED !!` 与 r176 同因（`na5`，非本轮引入）。
- 电池结束文件已恢复（`git diff --numstat` 仍只有 code_generator +53/−3）。

### 4.4 零触碰 38 案 + 红线

`zerotouch177.py`（r176 模板，r177 产物 vs r176 产物）：

- 38 案：37 SAME + 唯一允许例外 `r164/request_final` DIFF 且 == 本轮 request 产物；非允许差异 0。
- 红线逐单元：subprocess `_check_timeout` / `_execute_child`(units=2) / `_on_error_fd_closer` /
  `list2cmdline` / `call` / `run` 全 BYTE-SAME；cookiejar 十一条（含 `_normalized_cookie_tuples`）
  全 BYTE-SAME。

### 4.5 卫生

`scripts/validate_region_generator_signatures.py`：`统计: 14 个错误, 6 个警告`（与基线一致；
脚本 exit 1 是既有口径）。

## 5. 零触碰/卫生核对

- `git diff --numstat`：`53  3  core/cfg/code_generator.py`（唯一）。
- 未改 `.trae/`；未 commit/push/stash；无 `V177DBG`；无 `_merge_` 新名。
- 探针均在 `D:\temp\opencode\cl_layout\r177*`（仓库外）；`fix177.py` 具备 `count==1` anchor、
  utf-8-sig、CRLF 保持、`py_compile` 与幂等（二次 `--check` = 0 hunk）。

## 6. 产物索引

| 文件 | 内容 |
|---|---|
| `r177/fix177.py` | 唯一补丁（幂等/锚点/编译校验） |
| `r177/battery177.py`、`battery_stdout.txt` | 458 电池与输出（17/458） |
| `r177/rdel.py`、`work/diff_del.txt` | `__del__` 复现、判官、逐指令差分 |
| `r177/probe_regions.py`、`probe_ast4.py`、`probe_gen.py` | 区域/AST/生成端只读探针 |
| `r177verify/corpus_judge_v177.txt`、`raw_judge_*.txt` | 五语料读数 |
| `r177verify/unit_del_judge.py` | `Popen.__del__` 逐单元 Equal（41/41） |
| `r177verify/zerotouch177.py`、`zerotouch_stdout.txt` | 38 零触碰 + 红线 |
| `r177battery/ev/r161_regress_result.txt` | 电池逐案结果 |
