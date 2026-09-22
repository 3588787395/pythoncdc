# Round 36 · arm-design

 landed 基线：HEAD `703be216`，`core/cfg/region_ast_generator.py` 原始 sha256[:20] `92c8c2aabdcd37b9f32b`
（2984322 字节、统一 CRLF 48418、UTF-8 BOM）。本轮所有「改前」读数均对该字节成立。

## 一、目标池（实测，官方尺 `logs/landed_d1.jsonl` 6 行 + `logs/landed_d2.jsonl` 12 行）

`pool36.py` 对 landed 重读全索引：**files 402 partial 29 sum_deficit 99 deficit1 6 deficit2 12**。
deficit-1 名单与 Round 34/35 同一批（`instance 31/32`、`replace_utils 8/9`、`strategy 23/24`、
`default_event_source 13/14`、`realtime_event_source 11/12`、`matcher 16/17`），逐条读数一致；
靶子 `fly_api/base.pyc 39/41` 落在 deficit-2 池。

电池本轮扩到 **合成 44 片 / 锚点 105 个**（`lists36.py`）：合成侧 = Round 35 的 39 片 + R35-B 的
5 片见证/控制/反例；锚点侧 = Round 35 的 104 个 + `plugin_system_trade/function.pyc`（R35-B 靶子）。
两条 landed 基线：`logs/b44_landed.jsonl`（44 行）、`logs/a105_landed.jsonl`（105 行）均 0 error，
且 b44 对 b39 基线的 A/B 为 `SAME=39 IMPROVED=0 REGRESSION=0`（新增 5 片全过，39 片产物字节未变）。

「改前」侧的复用前提本轮逐项重证：
1. `r36c.py build` 断言 `mirr_head/core/cfg/region_ast_generator.py` 与工作区文件**字节全等**；
2. `head` 臂对 d2list（含靶子）重读，与 `landed_d2.jsonl` 的 A/B 为
   `TALLY SAME=12 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0`——`ab` 的 SAME 判据是产物 sha256 相等，
   故这是**字节级**等价证明，不是计数等价；
3. Round 35 的 `round35/logs/g4_r35b.all.jsonl`（402 行、0 error）路径集与 `all402.txt` 全等，
   而 r35b 臂即当前 landed 字节 ⇒ 它直接充当全量 G4 的「改前」侧（373 个全匹配文件）。

## 二、Round 35 移交问题的答案

移交项 1「R35-B 族的池内残余」：**零**。`probe3_36.py` 对 d1+d2 池全部 30 个缺陷函数重编译产物、
按 strict hunk 形状分类，无一条属于 `['POP_EXCEPT','POP_EXCEPT','LOAD_CONST','RETURN_VALUE']`
清理尾声形（`logs/probe3_epilogue_residuals.txt`）。该线不再便宜，除非出现池外证据。

## 三、目标选择（按取证成本排序）

| 候选 | 池内形状 | 一次判据的成本 | 结论 |
| --- | --- | --- | --- |
| `fly_api/base.pyc` 孪生 `get_/has_close_position_type` 30/9、27/6 | 整条 `for` 语句连同体内赋值一起消失 | 可合成最小重现 | **选为本轮靶** |
| `strategy :: tick_worker_thread` 268/247 | 单个 29 条指令的 elif 臂缺失，且首合取支被借走 | 需先定臂归属 | 留下一轮 |
| `matcher :: match` 713/689 | 281 删除 + 259 插入的换位，另丢一条 `STORE_FAST` | 需先拆排序 | 留下一轮 |

选它的决定性理由不是「便宜」，而是它**可能是纯机械故障**——见 §四，事后证明成立。

## 四、G0 边界电池（7 片，`test_repros/round36_for_loop_dropped/`）

靶子一手形状（原始行号 428–433）：

```python
def has_close_position_type(self, transaction_code):
    for i, c in enumerate(transaction_code):
        if c.isdigit():
            transaction_code = transaction_code[:i]
            break
    return transaction_code in self._store
```

`shapes36.py` 造 7 片，`g0_run36.py` 双尺读（官方 `bytecode_diff` + strict 全函数逐条），
判决表（`logs/g0_head.txt` 与 `logs/g0_landed.txt` 同表；`logs/g0_r36a.txt` 见 §六）：

| 片 | 与靶子的差异（唯一改动） | landed | 缺口 |
| --- | --- | --- | --- |
| `r36_01_witness_for_body_is_if_with_sideeffect_break` | 靶子同形 | FAIL | −21 |
| `r36_02_witness_exit_is_call_with_default` | 出口是 `STORE.get(tc, 3)` | FAIL | −21 |
| `r36_03_control_statement_between_loop_and_exit` | 循环与出口之间再夹一条语句 | FAIL | −21 |
| `r36_04_control_break_without_sideeffect` | if 臂内只有 `break` | **PASS** | — |
| `r36_05_control_for_else_break_target_differs` | 加 `else:` 子句 | **PASS** | — |
| `r36_06_control_body_has_leading_statement` | if 之前多一条 `n = len(tc)` | FAIL | −25 |
| `r36_07_control_no_break_at_all` | 臂内不 `break` | **PASS** | — |

由此定出判别式，且**否证了两个先前假设**：
- 「汇合块同时充当函数尾才触发」被 `r36_03` 否证（中间隔一条语句照样整块丢）；
- 触发条件与出口语句内容、体内语句条数无关，只与 **①循环无 else（break 目标即自然出口）
  ＋ ②`break` 所在臂还带有自己的前导语句（臂不是纯跳转）** 二者有关。

## 五、根因：一处被上层异常兜底吞掉的 TypeError

诊断代理（150 轮耗尽、未交 `ANALYSIS.md`）留下的唯一硬证据是其崩溃扫描：逐行给区域生成挂
异常探针。最大的一份 `logs/diag_p7c_crashscan128.txt`（输入名单同名 `diag_p7c_roster.txt`，
另存更短的早先一版 `logs/diag_p7b_crashscan.txt`，48 行＝18 语料＋30 电池件）128 行里
**只有 21 行是语料 `.pyc`（402 个中的 21 个），其余 107 行是 `test_repros/` 合成件**；
被扫到的 21 个语料文件中只有靶子崩溃——`2x TypeError @ region_ast_generator.py:4824 in
_fold_break_to_return`。所以「全语料只有靶文件崩溃」这句不能由该扫描承担，本轮把它交给
G4 全 402 A/B 实测（`SAME=401 IMPROVED=1 REGRESSION=0`，见 §七）。代理自己的 in-memory
修补产物（`logs/diag_p10_agentpatch_product.txt` 把循环摊平成 `enumerate(tc)` / `c.isdigit()`
三条裸表达式语句）被本轮边界电池直接否证，未采纳。根因由编排方接手闭合：

`_loop_generate_for`（`:4279`）的 break→return 折叠在 `:4812` 定义闭包 `_fold_break_to_return`，
取臂容器写作

```python
4817|                            _orelse = s.get('orelse', [])
4824|                            elif (len(_orelse) == 1 and ...):
```

`dict.get(k, 默认)` 的默认值只在**键缺失**时生效；本项目的 If 节点存在
`{'orelse': None}` 这一表示（`:17457`、`:34766`、`:36939`、`:37090`、`:44441` 等发射点写
`else_stmts if else_stmts else None`），于是 `_orelse` 取到 `None`，`len(None)` 抛 TypeError。
折叠只在 `_break_to_return_map` 非空时才被调用（`:4809`），而该表要求 break 后继块的
`get_block_role` ∈ {RETURN, RETURN_NONE}（`:4798-4800`）——这正是「循环无 else」的形状；
`r36_04` 的臂是 `len(_body)==1` 的纯 `break`，先命中 `:4818` 的 if 分支而够不到 `:4824`，
`r36_07`/`r36_05` 则表空根本不进折叠。三个 PASS 控制因此各自站在崩溃点的另一侧。

异常向上冒泡后被区域生成的兜底 `except Exception`（`:1681-1683`，包住 `:1682` 的
`_generate_region`）吞掉，该区域改走 `_generate_degraded_statements`（`:1688`）逐块降级，
整个函数回退成只剩尾 `return` 的退化产物——
所以症状是「整条 for 语句连同体内赋值消失」而不是报错。核心自己的文档已写明这条契约：
`_normalize_stmt_lists`（`:573`）docstring 指名「循环 break 折叠…按 `s.get('orelse', [])` 取值后
直接 len()/迭代，键存在且值为 None 时默认值失效 → TypeError，最终被上层异常兜底把整个函数
回退为 pass（灾难级语义丢失）」，并声明修复分两层（发射点统一 list ＋ 汇总处归一）。
归一发生在 `generate()` 汇总处（`:1697`），**晚于**区域生成，故区域生成内部自建的 If 节点在
折叠时仍未被归一；同一个折叠的 while 路径（`_loop_generate_while`，`:4935`）已改用安全惯式
`_orelse = s.get('orelse') or []`（`:6381`），for 路径 `:4817` 是同一处逻辑的漏网第二半。
同族还有第三处未触发者 `:2118`（`_build_function_def` 内的同款读取），池内无崩溃证据，
本轮不动，记入台账。

## 六、候选 R36-A（单条同层判据）

**判据**：break→return 折叠读臂容器时，`None` 与缺键一律按语句容器表示不变量归一为空表——
即 for 路径的取值式必须与 while 路径的既有归一读取同式。
**同层性**：读的是「节点表示不变量」，不读变量名/常量/绝对偏移/指令条数/认领历史；
不改折叠的识别条件与 AST 映射（`None` 与 `[]` 都表示「无该子句」），只在原先必然抛 TypeError
的那一个求值点上停止抛错，把决定权交还给折叠自身的结构判据（臂不是单条 `break` ⇒ 不折叠 ⇒
不标记、循环与体内赋值照常发射）。

补丁（`spec36a.json`，1 处编辑、增删行数 0，锚点两行在 2984322 字节文件中唯一）：

```python
-                            _orelse = s.get('orelse', [])
+                            _orelse = s.get('orelse') or []
```

G0 实测：`head` 臂 `PASS 3/7`（四条 FAIL 全为 −21/−25 整块丢失），`r36a` 臂 `PASS 7/7`，
四个失败形状全部翻正且三个通过形状逐条未变。靶子文件在 `r36a` 下
`39/41 → 41/41`（G1 d2 池 `IMPROVED=1 SAME=11 REGRESSION=0`），产物文本
`baseOK.py:319-324` 与原始源码逐字符一致。

## 七、门禁

| 门 | 内容 | 结果 |
| --- | --- | --- |
| G0 | 7 片边界电池 head vs r36a | `3/7` → `7/7` PASS |
| G1 | deficit-1 池 6 文件 | `SAME=6 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0` |
| G1 | deficit-2 池 12 文件（含靶子） | `IMPROVED=1(base 39/41→41/41) SAME=11 REGRESSION=0` |
| G2′ | 合成 44 片对 landed 基线 | `SAME=44 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0` |
| G3 | 锚点 105 对 landed 基线 | `SAME=105 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0` |
| G4 | 全量 402 文件 A/B | 见 `OUTCOME.md` |
| G4′ | 每个变更产物的 strict 尺复读 | 见 `OUTCOME.md` |
| G5 | `single` 靶子 + canary | 见 `OUTCOME.md` |
| G6 | `batch --index pyc_index.json --all --round 36` | 见 `OUTCOME.md` |
| G7 | `stats` | 见 `OUTCOME.md` |
