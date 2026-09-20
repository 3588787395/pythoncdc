# Round 13 — Wave 2 诊断（编排者实测，全部结论有可复跑证据）

判据：`_r10_strict_check.py`（严格尺子）。探针组：`test_repros/round13d/`。

## 0. 结论一句话

`if/elif/else` 链归约后，**链尾后续语句被吸进某个分支**，同时留下一条多余的
不可达隐式 `return None` —— 这两件表面不同的事（`+1/+2` 与 `-1` 指令数）是
**同一个区域归约缺陷**的两个症状。4 个最小复现 + 3 个负对照全部按预期通过。

## 1. 缺陷体量分布（实跑 234 个缺陷函数中的 seq_len 子集，n=147）

`delta = decomp指令数 - orig指令数`（过滤 NOP/CACHE/PRECALL/EXTENDED_ARG）

| delta | 函数数 | 判读 |
|---|---|---|
| +2 | 22 | 尾部多一条不可达 `LOAD_CONST None; RETURN_VALUE` |
| +1 | 26 | 多一个裸 `POP_TOP`，或同类重复 |
| +3..+12 | 15 | 语句级重复/布局重组 |
| -1 | 24 | **少一条 `JUMP_FORWARD`** ← 链吸收的典型副作用 |
| -2..-95 | 60 | 整段区域被吞（另一类，见 §5） |

正向合计 64，峰值集中在 +1/+2；`-1` 有 24 个。**两者同源**（§3 的 s2/s7/s10 是
-1，s8 是 +2），所以一次修复的理论上限是 ~72 个函数，而不是按表面数字分两次修。

## 2. 排除「编译器小版本差异」这条退路（先做证伪，再谈修）

Round 11/12 多次用「3.11.7 代码生成不同」为差异开脱，本轮先实测：3.11.7 对
**各臂全 return** 的 if/elif/else **不发射**尾部隐式 return：

```
if/else 全返回              tail: LOAD_CONST 1, RETURN, LOAD_CONST 2, RETURN   （无多余）
if/elif/else 全返回         同上，无尾部 LOAD_CONST None/RETURN_VALUE
存在可达落空路径时          才发射恰好一条 LOAD_CONST None, RETURN_VALUE
```

⇒ `get_covered_amount`（orig=171 decomp=173）尾部出现**两条**
`LOAD_CONST None; RETURN_VALUE`，不可能由编译器产生，必是产物 AST 的问题：

```
 idx  orig                     decomp
 170  ('None','RETURN_VALUE')  ('None','RETURN_VALUE')
 171  -                        ('None','LOAD_CONST')     <<< 多余
 172  -                        ('None','RETURN_VALUE')   <<< 多余
```

## 3. 最小复现（`test_repros/round13d/r13d_chain_absorption_probe.py`，7/7 PASS）

走完整流水线：源码 → 3.11.7 编 pyc → 项目反编译器 → OK.py → 重编 → 严格逐指令对照。

**R13-W2-A 分支以循环区结束 → 链后语句被吸入该分支**（s2 / s7 / s10，均 -1）

```
正确源码                          反编译产物（错）
if c: return 1                   if c: return 1
elif r:                          elif r:
    for d in r: pass                 for d in r: pass
else: return 2                       y = 7          <<< 被吸进 elif
if c: return 3                       if c: return 3 <<< 被吸进 elif
else: return 4                       else: return 4
                                  else: return 2
```

语义被改：原语义「链尾无条件执行」，产物变成「仅当 `elif r` 成立才执行」。
`for` 换成 `while`（s7）、链尾加多条语句（s10）同样复现 ⇒ 与语句数无关，
与「该臂的出口是循环区的 fall-through」强相关。

**R13-W2-B 链无 else 臂 → 链后语句被吸入新建的 else 臂**（s8，+2）

```
正确源码                          反编译产物（错）
if c: return 1                   if c: return 1
elif r:                          elif r:
    for d in r: pass                 for d in r: pass
if c: return 3                   else:
else: return 4                       if c: return 3   <<< 无中生有的 else 臂
                                     else: return 4
```

原始 CFG 的 `if/elif` **没有 else 边**，产物凭空新建了一条 else 边承载后续语句 ——
直接违反「归约后父区域的 then/else 列表引用子区域的入口，而不是子区域的所有块」。

**负对照（必须保持 MATCH，否则判据不成立）**：
`elif` 臂体是普通赋值（n1）、`if` 臂落空（n2）、`elif` 臂以显式 return 结束（n3）
—— 三者均 MATCH ⇒ 触发条件精确锁定为
**「臂体以可落空的循环区结束」+「链后还有语句」**，不是一般性的 if 链问题。

## 4. 修复方向（给修复工程师，不含具体代码）

按区域归约表述，禁止用 `op[offset] == FOR_ITER` 这类跨区启发式：

- **识别条件**：一个 `if/elif/else` 区间的某臂归约后其区域出口 `exit(B)` 不是该臂
  的唯一终结（即该臂含 fall-through 型子区域，循环区是其内部抽象节点），而该区间的
  merge 后继 `M` 同时是**其他臂**的可达终点。
- **归约方式**：此时 `M` 必须保持为该 if 区间整体的**单一出口节点**，继续留在父区域
  的语句序列里；臂的内层只允许引用子区域**入口**，不得把 `M` 的块并入臂的 then/else 列表。
- **AST 映射**：链后语句映射为父区域的兄弟语句（`If(...)` 的后续 `stmts`），
  而不是 `orelse`/某臂 `body` 的成员；无 else 边时 `orelse` 必须保持为空列表。

预期连带消掉 §2 那条不可达的尾部 `return None`（它是吸收之后多出来的落空路径）。

## 5. 另一类，尚未定位到最小复现（不假装已解决）

`-20 .. -95` 的巨型指令缺失（`get_index_stocks_local` 151→56、`_process_tick_order`
162→104、`can_resume_strategy` 89→57、`quote.run_individual_transform` 364→321 等），
是整段区域被吞，**不是** §3 的布局问题。未建最小复现，不下结论。

## 6. 负对照与方法论自我纠正（重要）

`else: return None` 这种退化文本形态出现在 **135** 个 OK.py 中，但
`IQEngine/plugins/plugin_system_trade/apiOK.py` 含 **52** 处却严格尺子 **0 缺陷**
⇒ 「退化 else」不是缺陷指纹，禁止拿它做批量改写依据。我最初按文本形态统计它，
属于会误导修复的口径，已在此更正：判定只用逐指令 delta 与复现流水线。

同理，`Quote.check_industry_code` 的
`CONTAINS_OP invert 0→1` + `POP_JUMP_IF_TRUE→IF_FALSE` 是**联合反演**
（操作数取反与跳转极性同时翻转，控制流等价）。**本轮不改尺子**，
只让生成器忠实保留原始区域的极性与落点；把「放松判据」当修法是投机取巧，明确禁止。

## 7. 复现命令

```
PYTHONIOENCODING=utf-8 python test_repros/round13d/r13d_chain_absorption_probe.py   # 7/7 PASS
PYTHONIOENCODING=utf-8 python _r13_gate.py --targets <pyc清单> \
    --baseline .trae/specs/.../rounds/round13/baseline_strict_ok351.txt \
               .trae/specs/.../rounds/round13/baseline_strict_partial51.txt         # 变差自动回滚
```

逐函数首差异对照：`D:/Temp/r13_differ.py` 的 `show(pyc, okpy, 函数名片段)`。
全量明细（未截断）：`D:/Temp/r13_partial_full.txt`、`D:/Temp/r13_ok_strict_full.txt`。
一次修复可翻正多文件的杠杆清单：`leverage_map.txt`。

---

# 追加：R13-W2-D「循环内的 `return` 被降级为 `break`」— 本轮最高优先

这是实测出来的**第二个独立类**，与 §3 的链吸收**不是**同一根因，代码路径不同。
它同时解释 **3 个「只差 1 个函数」的文件**，是本轮性价比最高的修复。

## D.1 三处实证（均为逐指令实测，delta 都是 -1）

| pyc | 函数 | orig/decomp | 备注 |
|---|---|---|---|
| `IQEngine/core/plugin_manager.pyc` | `PluginManager.set_engine` | 194/193 | |
| `IQData/manager/plugin_manager.pyc` | `PluginManager.set_engine` | 184/183 | 同名模块的另一份拷贝 |
| `IQEngine/plugins/plugin_system_control/__init__.pyc` | `AccountPlugin._terminate` | 43/42 | |

`_terminate` 的首差异（实跑输出）：

```
 idx  orig                     decomp
  32  ('None','POP_TOP')       ('None','POP_TOP')
  33  ('None','LOAD_CONST')    ('<JUMP>','JUMP')        <<< return 变 break
  34  ('None','RETURN_VALUE')  ('<JUMP>','JUMP')        <<<
  35  ('<JUMP>','JUMP')        ("'sys'",'LOAD_GLOBAL')  <<<
```

## D.2 语义后果（这不是字节码洁癖，是行为被改）

产物源码 `plugin_system_control/__init__OK.py:40-48`：

```python
def _terminate():
    for func in (current_process, current_thread):
        instance = func()
        if isinstance(instance, Instance):
            instance.terminate()
            break          # 产物：跳出 for，继续执行 sys.exit(0)
    sys.exit(0)
```

原始字节码在该分支里是 `LOAD_CONST None; RETURN_VALUE` —— **函数直接返回，
`sys.exit(0)` 根本不该被执行**。产物把它写成 `break`，于是找到 Instance 时
也会再调 `sys.exit(0)`，多杀一次进程。这是真实的行为差异。

`set_engine` 同形：原始 `if plugin_module is None: del self._plugin_list[idx]; return`
被写成 `break`，于是提前退出被改成「跳出内层 for，继续 sort 并写 plugin_dict」。

## D.3 实测出的精确判据（**我最初的猜测被自己的探针证伪，以下为实测**）

我原先猜的判据是「循环内 return + 循环后有语句」。**错** —— 该形态 `p1` 实测 MATCH，
反编译器处理正确。用 `test_repros/round13d/r13d_return_vs_break_probe.py`
（8 项断言全 PASS + 2 项测量）逐一切分后，真判据是：

| 形态 | 实测 |
|---|---|
| `if x: return`（return 是分支内**第一条**语句），循环后有语句 | **MATCH**（正确） |
| `if x: return x`（带返回值），循环后有语句 | **MATCH**（正确） |
| `if x: del xs[i]; return` | **MISMATCH** → `break` |
| `if x: x.close(); return` | **MISMATCH** → `break` |
| `if x: y = 1; return` | **MISMATCH** → `break`（**赋值也触发**，与 POP_TOP 无关） |
| `if x: x.a(); x.b(); return`（两条前导语句） | **MISMATCH** → `break`（只吞 return 本身） |
| `for ...: x.close()` 之后在**循环外** return | **MATCH**（正确） |
| 分支内确实是 `break` | **MATCH**（正确，负对照） |

⇒ 精确条件：**裸 `return`（返回 None）不是所在分支的首条语句，且位于循环区域内，
且循环区域之后同函数还有语句** 时，被降级为 `break`。
带返回值的 `return` 不受影响 —— 说明缺陷出在「`LOAD_CONST None; RETURN_VALUE`
这一对指令的归属判定」上，而不是语句序列切分上。

**归约层面表述**（给修复工程师，禁止跨区启发式）：

- **识别条件**：某块终结于 `LOAD_CONST None; RETURN_VALUE`，且该块位于某个循环区域的
  回边支配范围内，而该循环区域的 exit 之后**在函数区域里仍有兄弟语句**；
  此时该块的落点是**函数出口**，不是循环出口。
- **归约方式**：该块作为函数级**终结抽象节点**参与归约，不得与循环区域的 merge 合并；
  循环区域归约只收集真正落到循环 exit 的边。
- **AST 映射**：`Return(None)`。`Break()` 仅当该块落点 == 最内层活跃循环的 exit 时才允许产生。

## D.4 现成的复现与验收

- 本轮新增：`test_repros/round13d/r13d_return_vs_break_probe.py`（**5 行最小复现**，
  `p2/p4/p5/p6` 四项 MISMATCH，`p1/p3/n1/n2/n3/n7` 六项 MATCH）。
- 上一轮测试工程师另有 `test_repros/round13/r13_01_return_becomes_break.py`
  （以 `_terminate` 为原型，实测 MISMATCH）。两套互为独立验证。

验收标准：

1. `r13d_return_vs_break_probe.py` 中 `p2/p4/p5/p6` 由 MISMATCH → MATCH，
   且 `p1/p3/n1/n2/n3/n7` **保持 MATCH**（否则是把判据放宽成「循环内一律 return」，
   会引入新回归）；
2. D.1 表中 3 个文件由「只差 1 函数」→ **100% 严格一致**（官方口径同步转 ok）；
3. `_r13_gate.py` 全量复跑零回归（变差自动回滚）。

**先修 D 再修 §3**：D 的判据已经实测清楚、复现只需 5 行，一次翻正 3 个文件；
§3 覆盖面更大（约 72 个函数）但判据更复杂，风险更高，紧随其后。


