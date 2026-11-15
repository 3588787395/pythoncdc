# RESULT175 — subprocess SP1 CALLEX（with-item CALL_FUNCTION_EX）71→73/78

> 仓库 `F:\Downloads\pythoncdc-main`；解释器 `D:/Python/python.exe -I -X utf8`，cwd=仓库根。
> 补丁 `D:\temp\opencode\cl_layout\r175\fix175.py`（1 文件 / 2 anchor，count==1、utf-8-sig BOM 感知、
> LF/CRLF 保持、`py_compile`、幂等；从改前快照重打 = 逐字节同 sha `DF06FA9D…`）。
> 判官 `scripts/pyc_verify.py single <pyc> --source <产物>`（matching_iter 配对，未按名字自配）。

## 0. 读数

| 语料 | r174 | r175 | 产物 |
|---|---|---|---|
| subprocess | 71/78 | **73/78（93.59%）** | 69864 B `1866ef58` → **69910 B `45a98b3f`** |
| request | 194/194 | **194/194** | 87699 B `db2172e8` **逐字节 SAME** |
| difflib | 62/62 | **62/62** | 67855 B `d70df600` **逐字节 SAME** |
| tarfile | 156/160 | **156/160** | 89892 B `fcb8a7fb` **逐字节 SAME** |
| cookiejar | 100/105 | **100/105** | 68916 B `0d13ea83` **逐字节 SAME** |

subprocess 失败 7 → 5（`call`、`run` 转 EQUAL）：
`Popen.__init__`、`Popen.__exit__`、`Popen.__del__`、`Popen._internal_poll`、`Popen._wait`
（SP3/SP4/SP5/SP6/SP7，本轮未动）。

## 1. 复验缺陷（r170 recon 定性属实）

复现 `repro/sp_callex_with.py`（`with Popen(*popenargs, **kwargs) as p:` + try/except）：
产物 `with kwargs as p:`，判官 `1/2`（failure bytecode）。
控制组全部 EQUAL：`return Popen(*a)`、`return Popen(a, **kw)`、`return Popen(*a, **kw)`、
`x = m(*a, **kw)`、`m(*a, **kw)` —— 缺陷**只在 with-item 上下文**。

`dis` 原始（call 单元，43 条）：`LOAD_GLOBAL NULL+Popen; LOAD_FAST popenargs; BUILD_MAP 0;
LOAD_FAST kwargs; DICT_MERGE 1; CALL_FUNCTION_EX 1; BEFORE_WITH`。
产物（38 条）：`LOAD_FAST kwargs; BEFORE_WITH`（r170recon/diff_subprocess.txt #24：
delete `orig[0:1]` + `orig[2:6]`）。

## 2. 根因与修复谓词

根因在**识别层**而非重建层：`core/cfg/region_analyzer.py:16887`（`_extract_with_items`）
按 ctx 白名单收集 BEFORE_WITH 之前的值生产链，白名单含 `BUILD_MAP`/`CALL`/`KW_NAMES`
但**缺 `DICT_MERGE` 与 `CALL_FUNCTION_EX`**。ctx_expr 因此只剩
`LOAD_GLOBAL, LOAD_FAST popenargs, BUILD_MAP 0, LOAD_FAST kwargs`；
`region_ast_generator._generate_with`（L48006→L48097 `expr_reconstructor.reconstruct`）
见到的是「被调对象 + 实参装载 + 空 dict」这条不完整链，按栈顶残留值归约为 `kwargs`
（`ast_generator_v2.ExpressionReconstructor` 的 CALL_FUNCTION_EX 分支根本没被喂到）。

修复谓词（只增）：ctx 白名单追加 `'DICT_MERGE', 'CALL_FUNCTION_EX'`，
即「合并/扩展调用是同一调用表达式的组成部分」——`f(**kw)` 的 `BUILD_MAP 0; LOAD kw;
DICT_MERGE 1` 与 `f(*a)` 的 `CALL_FUNCTION_EX 0` 都随值生产链一并收集。
重建器既有 CALL_FUNCTION_EX/DICT_MERGE 分支（`ast_generator_v2.py:2422/1778`）随之生效。

判官：`call` EQUAL（43/43 instr，CFG 13/13 · 17/17）；`run` EQUAL（137/137，34/34 · 55/55）。

## 3. 文本变化（只有 subprocess 2 行，均更接近源码）

`r174judge/products/subprocess_now.py` → `r175 …/subprocess_now.py`：
1. L389 `with kwargs as p:` → `with Popen(*popenargs, **(kwargs)) as p:`（源码 `subprocess.py:389`）
2. L548 `with kwargs as process:` → `with Popen(*popenargs, **(kwargs)) as process:`（源码 `:548`）

`**(kwargs)` 的括号是本反编译器既有写法（`check_call` 的 `retcode = call(*popenargs, **(kwargs))`
一直如此且 EQUAL），重编后 CALL_FUNCTION_EX 逐位一致。
r174 的 `capture_output` 改动（`or` + `else:`）**保留未动**（diff 上下文可见）。

## 4. 458 电池（硬门）

`D:\temp\opencode\cl_layout\r175\battery175.py`（由 `...fresh\tarfile167\r170_regress.py` 复制，
只改 `TMP/OUTDIR/EV` 到 `D:\temp\opencode\cl_layout\r175battery\`，仓库内脚本未改），
先删 scratch 再跑，`exit=0`：
- **TEXT-DIFF = 17 / 458**，集合与允许集**逐案相同**（E161 六 + v111 三 +
  `mk_iterencode/yp2/te_variants8/pc9/pm1/E3_andnot_nochainstmt/fdt/pc12`），**17 案全 BYTE-EQUAL**。
- 与 r174 逐案 (TEXT, 签名) 比对：**changed statuses = 0**（`work/cmp_battery.py`）。
- `C7_skipedge` **TEXT-SAME**。`R110 案: 169 / TEXT 状态一致 161 / 签名一致 167`（= r174）。
- `REG-10: CHANGED !!` 与 r174 同因（`na5`：TEXT-SAME 但签名自 r110 起已变），非本轮引入。

## 5. 红线 / 零触碰

- **红线逐单元字节核验**（`verify/j_redlines175.py`，纯文本切片，未跑反编译器）：
  subprocess `_check_timeout`/`_execute_child`(×2 双 class)/`_on_error_fd_closer`/`list2cmdline`
  **BYTE-SAME**；cookiejar 整产物逐字节 SAME，七条 + r174 三案逐单元 **BYTE-SAME**。
  判官侧 corroborate：这些单元不在失败名单（EQUAAL）。
- **零触碰 38 案**（`verify/j_zerotouch175.py` → `verify/zerotouch_v175.txt`）：
  37 SAME + `r164/request_final`（唯一允许例外，DIFF 且 == 本轮 request 产物 YES），
  **非允许差异 0 → PASS**。

## 6. numstat / 卫生 / 其它

```
12  1  core/cfg/region_analyzer.py
```
`scripts/validate_region_generator_signatures.py` → **统计: 14 个错误, 6 个警告**（= v172/v174 基线）。
仅改 1 文件；`.trae/` 未写；未 commit/push/stash；仓库内无探针、无 `V175DBG`；
`.trae` 内旧脚本未改；`fix175.py` 二次运行 = 0 hunk（幂等），从改前快照重打 = 同 sha。

## 7. 证据索引（`D:\temp\opencode\cl_layout\r175\`）

| 文件 | 内容 |
|---|---|
| `fix175.py` | 补丁（2 anchor，count==1；`work/pristine/` 上重打同 sha `DF06FA9D…`） |
| `verify/j_corpus175.py` / `corpus_base.txt` / `corpus_e1.txt` / `corpus_final.txt` | 五语料改前/改后/复跑读数（final 与 e1 逐字节同 sha） |
| `verify/j_zerotouch175.py` / `zerotouch_v175.txt` | 零触碰 38 案 |
| `verify/j_redlines175.py` / `redlines_v175.txt` | 红线逐单元字节核验 |
| `work/diff_subprocess_r174_r175.txt` | 产物文本 2 行 diff |
| `work/diff_sub_after.txt` | 改后逐单元差分（73 EQUAL / 5 DIFF，含 call 43/43、run 137/137） |
| `work/cmp_battery.py` / `cmp_battery_out.txt` | r174↔r175 电池逐案比对（changed 0） |
| `battery175.py` / `battery_stdout.txt` | 458 电池与结果 |
| `work/probe175.py` / `work/probes/p1.py` `p2.py` `p3.py` | 9+10 形位探针（全 success；`p3` 模块根多上下文嵌套为既有缺口，改前后均失败） |
| `work/backup/` | 改前 3 个 core 文件快照 |
