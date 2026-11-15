# RESULT171 — cookiejar CJ4 CONTINUE（3 单元）+ CJ1 DOCESC（1 单元）

> 仓库 `F:\Downloads\pythoncdc-main`；解释器 `D:/Python/python.exe -I -X utf8`，cwd=仓库。
> 补丁 `D:\temp\opencode\cl_layout\r171\fix171.py`（3 文件 / 6 anchor，count==1、utf-8-sig（BOM 感知）、
> 逐字节 round-trip、行数核账、py_compile、幂等；从 pristine 重打 = 逐字节同 sha）。
> 判官 `scripts/pyc_verify.py single <pyc> --source <产物>`。

## 0. 读数

| 项 | r170 | r171 |
|---|---|---|
| cookiejar | 91/105 | **94/105（89.52%）** |
| `<module>`（CJ1） | Failure (Different bytecode) | **EQUAL** |
| `MozillaCookieJar.save`（CJ4） | Failure (flow) | **EQUAL** |
| `LWPCookieJar.as_lwp_str`（CJ4） | Failure (flow) | **EQUAL** |
| `CookieJar._normalized_cookie_tuples`（CJ4） | Failure (flow) | Failure（**未闭合**，见 BLOCKER） |
| request | 194/194 `9e3e7baf…` | 194/194 `db2172e8…`（文本 DIFF） |
| difflib | 62/62 `d70df600…` | 62/62 `d70df600…`（**SAME**） |
| tarfile | 155/160 `4dba499d…` | **156/160** `1fc7b487…`（文本 DIFF，+1） |
| subprocess | 69/78 `53d99059…` | 69/78 `b1926c86…`（文本 DIFF） |
| cookiejar 产物 | 70050 B `7c122a0d…` | 69312 B `83e691f2…` |
| 38 案红线 | 38/38 SAME | 37 SAME + r164req（= request 快照） |
| 458 电池 | 9 TEXT-DIFF / 全 BYTE-EQUAL | **21 TEXT-DIFF / 全 BYTE-EQUAL**（新增 12：R110×11 + V118×1） |
| 卫生 | 14 错 6 警 | **14 个错误, 6 个警告** |

## 1. 三处根因与修复谓词

### CJ1 `[v171-DOCESC]`（`core/cfg/code_generator.py`，`_generate_expr_stmt` + 新 `_v171_doc_literal`）
模块级 docstring 原为 raw 三引号、内含 7 处「反斜杠+换行」；旧码按普通三引号原样发，
重编译把该对字符当行连接吃掉（常量 938→924 B）。模块 docstring 在 3.11 是
`LOAD_CONST 0; STORE_NAME __doc__`（常量值进字节码 ⇒ 判官可见），函数/类 docstring
无指令引用。修复：只对 `indent_level == 0`（模块体）的 docstring 先对既有候选做
**语义回读核验**（`ast.literal_eval` 必须逐字等于原常量），通过即逐字返回；失败才按
raw 前缀 → 反斜杠双写 → repr 重建并再核验。四语料/电池实测：函数 docstring 零触碰。

### CJ4 `[v171-ITER-EXIT]`（`core/cfg/region_analyzer.py`，新 `_v171_iter_exit_merge` + 调用点）
`if <判据>: continue` / `: break` 在 for 体内时，NCPD 塌陷到循环边界
（as_lwp_str If@56 merge=48=header；save If@348 merge=326=header；
_normalized_cookie_tuples If@190 merge=564=内层 for 出口），于是 if 之后的同层语句被
吸进臂内、臂尾补冗余 continue。既有 continue-sink 守卫被 elif 守卫挡住，而
`_build_elif_region` 对该形态弃权（else 臂在嵌套 if 后有尾随语句 ⇒ 规则③）。
修复：在 elif 构造器弃权后调用一次——`then` 臂无条件离开本轮迭代/本循环
（JUMP_BACKWARD→header / JUMP_FORWARD 后继全在循环块集外）且 merge 落在循环边界
⇒ `merge=else_succ`、清空 else 臂；else_succ 是纯 break 桥时取桥落点（镜像 B133-V3R3）。

### CJ4 `[v171-ITER-EXIT-b]`（`core/cfg/region_ast_generator.py`，R40-A2 守卫）
R40-A2 把「then 臂全部跳出到循环头」的 merge 认成假臂本体；对 guard 形态
（then 臂是**裸 continue**、merge = 循环体尾语句块）会造成 r.append 缩进进 if 体
并多补一条 continue。修复：then 臂只含噪声/跳转指令（裸 continue）且 merge 末指令
是 `JUMP_BACKWARD→header` 时不认领。

### CJ4 `[v171-NESTED-ARM]`（同文件，`_process_if_blocks`）
父臂块列表重复收下嵌套 IfRegion 的 continue/break 臂尾块（无前向后继 ⇒ 被父臂当叶子），
父臂再发一次 ⇒ 多一条显式 continue。修复：过滤「入口 ∈ 本臂块集 且 merge 与本区域
同一块」的嵌套 IfRegion 的 then/else 成员；**宿主门 `self._current_loop is not None`**
（缺此门 r161c `nottail3` 红线判官 FAIL，实测）。

## 2. 未闭合单元（`_normalized_cookie_tuples`）

`IfRegion@284`（`if k == "expires":` 内层 `if max_age_set: continue`）merge=564、
else=[290, 326, 338, …] 吞掉同层兄弟 if 与 `else: rest[k] = v`（产品 1155–1180 行
出现伪 `elif/else` 嵌套）。已试：放宽 continue 判据（去 merge is header）无效；
放宽 R40-A2 裸臂判定到「只含条件求值」文本变而判官不变（已回退）；直接抑制认领则
`rest[k] = v` 摊平。该形态与 IF_ELIF_CHAIN 构造器规则③交叠，建议单开一轮。

## 3. 两个验收门的偏差（详见 BLOCKER_171.txt）

1. 四语料逐字节 SAME：request/tarfile/subprocess 文本变化（判官不减、tarfile +1）。
2. 458 电池 TEXT-DIFF 9→21（新增 12 条**全 BYTE-EQUAL**）。
   即 458/458 重编译字节码与 HEAD 相同；变化纯在渲染文本。
   严格门要求 = 回退 `region_analyzer.py` + `region_ast_generator.py` 两个锚点
   （只留 DOCESC）⇒ cookiejar 92/105、四语料逐字节 SAME、电池回 9。

## 4. 产物清单（`D:\temp\opencode\cl_layout\r171\`）

| 文件 | 内容 |
|---|---|
| `fix171.py` | 补丁（6 anchor / 3 文件），`--check` 只查锚点 |
| `BLOCKER_171.txt` | 未闭合单元 + 两门偏差 + 回退路径 |
| `battery171.py` | 458 电池（复制 r170_regress.py，仅改 TMP/OUTDIR/EV） |
| `r171verify/verify171.py` `corpora_raw.txt` `zerotouch_raw.txt` `judge_raw_*.txt` | 语料/红线读数 |
| `r171battery/ev/r161_regress_result.txt` | 电池结果（21 TEXT-DIFF / 全 BYTE-EQUAL） |
| `work/` | 探针（probe171a–j、dump 工具、各 t*.py 迭代产物、bisect171.py、exp1–10 实验） |
