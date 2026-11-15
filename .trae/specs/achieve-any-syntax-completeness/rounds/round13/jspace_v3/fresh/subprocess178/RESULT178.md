# RESULT178 — subprocess SP4 FINALLY-ARM 收口（Popen.__exit__，74→75/78）

> 仓库 `F:\Downloads\pythoncdc-main`；解释器 `D:/Python/python.exe -I -X utf8`（3.11.7）；cwd=仓库根。
> 单文件单 anchor：`core/cfg/region_ast_generator.py`（+64/−0）。未改 `.trae/`；未 commit/push/stash；
> 新名不含 `_merge_`；无 `V178DBG`。补丁 `D:\temp\opencode\cl_layout\r178\fix178.py`（2 anchor，
> `count==1`、utf-8-sig、LF/CRLF 保持、`py_compile`、幂等；从 `git show HEAD:` 重打 = 逐字节
> 同一 sha256 `0BFE1346…`）。

## 1. 差异复验（更正 recon170 SP4 卡的描述）

复现 `r170recon/repro/real/sp_Popen___exit___real.py`（逐字抽取 3.11 `subprocess.Popen.__exit__`）。
recon 卡写「finally 臂尾两条语句（`self._sigint_wait_secs = 0`、裸 `return`）丢失」——**实测不成立**：
产物 AST 里两条语句都在，`finally:` 主臂结构（含内层 `try/except TimeoutExpired`）完整。真实差异是
**函数末尾多出一条幻影语句**：

```python
        if TimeoutExpired:
            pass
```

- 指令 107→112；首个差异 idx=61：原 `122 LOAD_CONST None; RETURN_VALUE` → 产物
  `122 JUMP_FORWARD to 212`（正常路径 finally 结束后不返回，改跳幻影尾块）；尾部插入 6 条
  `LOAD_GLOBAL/POP_JUMP_FORWARD_IF_FALSE/LOAD_CONST/RETURN_VALUE/LOAD_CONST/RETURN_VALUE`；
  CFG 32→35 节点、53→57 边；异常表 12 条整体 −2 平移（recon 写 9 条是整模块上下文读数）。
- 幻影 `if <Exc>: pass` 在五语料产物里**唯一一例**（`subprocess_now.py:783`）。

## 2. 根因（函数:行号）

`core/cfg/region_ast_generator.py`：

1. `_generate_try`（L40226 起）在开头把**已发射** TryExceptRegion 的 `handler_entry_blocks`
   整组登记 `generated_blocks`（L40375-40377）。
2. 但 try/finally 的**异常路径副本**与正常副本结构镜像：副本的 IfRegion（`entry=416`）与内层
   TryExceptRegion（`entry=440`）因 entry 落在外层 try 的 `blocks` 里，被 `generate()` 的
   top_level 包含判定（L1856-1858）滤出，永不派发。副本内层 try 的 handler 匹配头块
   （`PUSH_EXC_INFO; LOAD_GLOBAL TimeoutExpired; CHECK_EXC_MATCH; POP_JUMP_FORWARD_IF_FALSE`，
   offset 496）因此既无发射 owner、也不在 `generated_blocks`。
3. `generate()` 的孤儿块释放（L2188-2247）给它建了 BASIC 区域；`_generate_basic_region`
   （L68605）→ `_generate_block_statements`（L69350）把它当普通块重建：块末条件跳转被当语句
   条件，操作数 `TimeoutExpired` 成为 test，真臂为空 ⇒ `if TimeoutExpired: pass`。
   既有 B86 纯异常协议块守卫（`_rag_is_pure_exception_protocol_block`，L68892）要求块内非噪声
   指令**全部**属于协议/栈案卷/跳转集，`LOAD_GLOBAL <Exc>` 不在集合内 ⇒ 不命中。

## 3. 修复谓词

新增 `_rag_is_unemitted_try_handler_entry`（L68939）并在块语句单一漏斗
`_generate_block_statements`（L69350）的 B86 守卫之后消费（L69412-69420）：

> block 未生成 ∧ 首条非噪声指令为 `PUSH_EXC_INFO` ∧ block 是某个**既不在
> `_generated_regions` 也不在 `_generating_regions`** 的 TryExceptRegion 的
> `handler_entry_blocks` 成员 ⇒ 整块登记 generated、发射空语句。

- 已生成区域的 handler 入口在 `_generate_try` 开头就进 `generated_blocks`，首条件直接排除；
- 正在生成的区域显式豁免，handler 臂仍走 `_generate_handler_body_statements`；
- 不命中时逐位保持（C3）。

## 4. r172 三处 try/finally 判据影响判定：**不受影响**

| # | 位置 | 内容 | 本补丁关系 |
|---|---|---|---|
| 1 | `region_analyzer.py:11737-11739` | `existing.try_blocks` 是本 region try 体块集**真子集**时不下移入口 | 未改分析端一行 |
| 2 | `region_analyzer.py:38970-38986` | `get_entry_region_for_block` 同入口多 TryExceptRegion、保护跨度互相包含时归外层 | 未改分析端一行 |
| 3 | `region_ast_generator.py:38294-38306` | `_generate_try_body` 生成侧 span 包含归属 | 同文件但相距 ~30k 行，未改 |

本补丁只读 `handler_entry_blocks` 成员关系，走的是块语句漏斗的**未发射副本抑制**；r172 的
三处判据读 `try_blocks`/`try_offset_*`/`parent`，且对应单元 `_execute_child` 两层 try 都会正常
发射（入口在 `_generate_try` 开头即登记 generated），守卫不可能命中。实测 `_execute_child`
（双 class，2 单元）r177→r178 **BYTE-SAME**、判官 EQUAL。

## 5. 验收读数

### 5.1 subprocess

- 失败名单 **4 → 3**：`Popen.__init__` / `Popen._internal_poll` / `Popen._wait`（`__exit__` 转 EQUAL，
  不再含 `__del__`/`call`/`run`/`_execute_child`/`_check_timeout`/`list2cmdline`/`_on_error_fd_closer`）。
- `units=75/78 success_rate=96.15%`。
- 单元判官：`<module>.Popen.__exit__: Success: Equal`；`diffunit` 逐单元：EQUAL，
  `instrs 107/107`、`nodes 32/32`、`edges 53/53`、异常表 12 条**逐条相同**。
- 产物 70034 B `9ab5e6bfdca7cc98` → **69988 B `557b9b0bfe9ef4e2`**；全文件仅 1 hunk：
  删除 `if TimeoutExpired:` / `pass` 两行（46 字节 = 28 + 18）。

### 5.2 四语料（与 r177 产物逐字节相同）

| 语料 | 读数 | 产物 |
|---|---|---|
| request | **194/194** | 87699 B `db2172e8f1a69af6` BYTE-SAME |
| difflib | **62/62** | 67855 B `d70df6006a50f33f` BYTE-SAME |
| tarfile | **156/160** | 89892 B `fcb8a7fbb7b246b2` BYTE-SAME |
| cookiejar | **101/105** | 68629 B `9c793bf9f0474ba1` BYTE-SAME |

文本变化形态：四语料零变化；subprocess 仅删幻影两行（源码无对应语句）。

### 5.3 458 电池（硬门）

`r178/battery178.py`（复制 `fresh/tarfile167/r170_regress.py`，只改 TMP/OUTDIR/EV 到
`D:\temp\opencode\cl_layout\r178battery`，仓库内脚本未改；先删 scratch 再跑）：

- **TEXT-DIFF = 17 / 458**，与允许集**逐案相同**（mk_iterencode/yp2/te_variants8/fdt/pc12/pc9/pm1、
  v111_m1_exact/v111_m2_no_genexpr/v111_two_if_diffmsg、E3_andnot_nochainstmt、E161 六案）；
  **17/17 全 BYTE-EQUAL**；无非允许新增。
- `C7_skipedge` **TEXT-SAME**。
- `R110 案: 169 / TEXT 状态一致 161 / 签名一致 167`（= r176/r177）。
- `REG-10: CHANGED !!` 与 r176/r177 同因（`na5`，非本轮引入）。
- 电池结束五文件已恢复；`git diff --numstat` 仍只有 `64 0 core/cfg/region_ast_generator.py`。
- 两次独立运行（`battery_stdout_run1.txt` / `battery_stdout_final.txt`）结果文件**逐字节相同**；
  最终 LF 工作副本 sha256 `0BFE1346…`（= `git show HEAD:` + 补丁）。

### 5.4 生成层/剪枝风险（ast.If 与语句总数前后）

| 语料 | If | stmt | Pass |
|---|---|---|---|
| request | 286 → 286 (+0) | 1725 → 1725 (+0) | 17 → 17 (+0) |
| difflib | 114 → 114 (+0) | 737 → 737 (+0) | 9 → 9 (+0) |
| tarfile | 325 → 325 (+0) | 1754 → 1754 (+0) | 16 → 16 (+0) |
| cookiejar | 240 → 240 (+0) | 1212 → 1212 (+0) | 8 → 8 (+0) |
| subprocess | 271 → 270 (−1) | 1127 → 1125 (−2) | 23 → 22 (−1) |

subprocess 的唯一减少项就是**源码不存在的幻影** `if <Exc>: pass`：`Popen.__exit__` 单元内
源码 If 5 / 改前 6 / 改后 5，stmt 15/17/15，Pass 1/2/1。**无任何源码语句减少** ⇒ PRUNE-RISK PASS。
（若把「无一减少」按产物计数字面理解，则唯一 −1 的 If 是待删幻影本身，已逐节点证明其无源码对应。）

### 5.5 零触碰 38 案 + 红线

- 38 案：37 SAME + 唯一允许例外 `r164/request_final` DIFF 且 == 本轮 request 产物；
  **非允许差异 0** ⇒ ZERO-TOUCH PASS。
- 红线逐单元 **21 项全 BYTE-SAME**：subprocess `_check_timeout`/`_execute_child`(2 units)/
  `_on_error_fd_closer`/`list2cmdline`/`call`/`run`/`__del__`；cookiejar 十一条
  （`add_cookie_header`/`make_cookies`/`set_cookie_if_ok`/`clear_session_cookies`/
  `clear_expired_cookies`/`as_lwp_str`/`MozillaCookieJar.save`/`user_domain_match`/`clear`/
  `set_ok_domain`/`_normalized_cookie_tuples`）。

### 5.6 卫生

- `git diff --numstat`：`64 0 core/cfg/region_ast_generator.py`（唯一）；`core/ast_nodes.py`、
  `core/cfg/ast_converter.py` 的 `M` 是 CRLF/stat 噪声（`git diff` 为空，开工前既存）。
- `scripts/validate_region_generator_signatures.py` → **统计: 14 个错误, 6 个警告**（与基线一致；
  exit 1 是既有口径）。
- `fix178.py`：anchor `count==1`；二次 `--check` = 0 hunk；pristine（`git show HEAD:`）+ 补丁
  = 工作树 sha256 `0BFE13464D08EFB95DD0D22FB746646B0258A0CF74A2A14250B5673E33CD0F43`。
- 探针/产物全部在 `D:\temp\opencode\cl_layout\r178*`（仓库外）；无 `V178DBG`；无 `_merge_` 新名。

## 6. 产物索引

| 文件 | 内容 |
|---|---|
| `r178/fix178.py` | 唯一补丁（2 anchor；幂等/编译校验/pristine 重打同 sha） |
| `r178/battery178.py`、`battery_stdout_final.txt`、`r178battery/ev/r161_regress_result.txt` | 458 电池与结果（17/458） |
| `r178/work/diff_ex.txt` / `diff_ex_fixed.txt` | 复现改前/改后逐指令差分 |
| `r178verify/products/*_now.py`、`corpus_judge_v178.txt`、`raw_judge_*.txt` | 五语料产物与判官原始读数 |
| `r178verify/diff_subprocess_v178.txt` | 整模块逐单元差分（__exit__ #43 EQUAL 107/107） |
| `r178verify/unit_exit_judge.py` | `<module>.Popen.__exit__: Success: Equal` |
| `r178verify/zerotouch178.py`、`zerotouch_v178.txt` | 38 零触碰 + 21 红线单元 |
| `r178verify/astcounts178.py`、`ast_counts_v178.txt` | ast.If/语句总数前后对比 |
| `r178verify/validator_v178.txt` | 签名验证器读数 |
