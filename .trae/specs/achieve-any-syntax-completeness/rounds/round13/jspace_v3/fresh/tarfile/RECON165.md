# RECON165 — tarfile 14 失败单元的分区、族谱与下一轮选族

> 只读侦察：仓库 F:\Downloads\pythoncdc-main 未写入任何文件（含 core/、scripts/、tests/、.trae/）。
> 本轮全部产物写在 D:\temp\opencode\cl_layout\r165\ 下。解释器 D:/Python/python.exe（3.11.7），命令 `-I -X utf8`，cwd=F:\Downloads\pythoncdc-main。

## 0. 读数与结论（先给答案）

- 重新反编译 + 判官：**146/160 = 91.25%**，14 单元名单与 r162 基线逐条一致（`judge_now.txt`）。
- 14 单元归入 **6 个候选族 + 3 个跨族单元**；按族做"削形实验"（把该族的源形手工还原后再判）实测边际闭合：

| 累积变体 | 读数 | 边际 | 闭合单元 |
|---|---|---|---|
| 基线 tarfile_now.py | 146/160 | — | — |
| +A 尾随/臂尾隐式 `return None` | 148/160 | **+2** | _check, add |
| +B `if<终结符>` 被融合成 elif/else | 150/160 | **+2** | _Stream.__init__, _Stream._read |
| **+C 多块条件（链式比较/BoolOp）链边归属** | **153/160** | **+3** | **itn, create_pax_header, gettarinfo** |
| +D 循环区归属（循环后块 / while 头语句） | 155/160 | +2 | TarFile.__init__, _load |
| +E BUILD_STRING/%-format 组 → 调用丢失 | 156/160 | +1 | list |
| +F 混合 `not or` 循环出口条件 | 157/160 | +1 | _Stream._init_read_gz |
| 剩余 | 157/160 | — | _FileInFile.read, next, main |

- **首选族 = C（多块条件在 if/elif 链中的链边归属）**：预计闭合 **3**（实测 +3），异常表/循环区零触碰，r156 已把它登记为"itn and 链链式比较成员"专项轮。
- **备选族 = A（尾随隐式 `return None` 注入）**：预计闭合 **2**（实测 +2），风险最低，与 C 单元零交集。
- C 若顺带覆盖 `while …: if not X or Y: break` 形态（族 F 同源），可得 **+4**；但 `_init_read_gz` 还需同轮带上 B 的 elif 修正。

---

## 1. 逐单元对照表

判据口径：判官先比基本块图（`is_control_flow_equivalent`），不等即 `Different control flow`；块图相等后才逐指令比，不等即 `Different bytecode`。因此下表给出的是**块图/指令级的实差**（用 bcdiff2.py / vdiff.py 从原始 pyc 与产物重编译 pyc 逐条对齐得到）。完整 80 行窗口见 `u01..u14*.txt`。

| # | 单元 | 真实源行 | 产物行 | 指令数 原/产 | 指令级实差（唯一或主要） | 一句判定 | 族 |
|---|------|---------|--------|--------------|--------------------------|----------|----|
| 1 | itn | 196-224（判定 209-222） | 102-121 | 118/118 | 仅 1 条边：`166 POP_JUMP_FORWARD_IF_FALSE ->424`（链的 `else: raise`）vs `->454`（汇合） | `elif A and <链式比较>` 的 else 边被挂到内层 if | **C** |
| 2 | _Stream.__init__ | 343-403 | 211-279 | 247/250 | +3 `POP_EXCEPT / LOAD_CONST None / RETURN_VALUE`：except 体内 `if not _extfileobj: close()` 之后的 `self.closed=True; raise` 被吸成 else 臂 → if 臂直落函数尾隐式 return；另 7 处臂尾多余 `return None` | except 臂"后续语句被吸成 else" | B（+A） |
| 3 | _Stream._init_read_gz | 474-503 | 330-362 | 138/146 | `if not s or s == NUL: break` 被拆成 `if s: if s == NUL: break else: break`（两处循环，各多 2 条 JUMP_FORWARD）+ `elif … raise` 融合 + 2 个多余 RETURN | 混合 `not or` 出口条件 + while-break 反转 | F（+B） |
| 4 | _Stream._read | 530-555 | 385-410 | 112/113 | +1 `JUMP_FORWARD`＝except 之后多出的 `break`（产物 405 行）；`if comptype=='tar': return` 被吸成 `else:` 使两条边落点改变 | 终结符 if 吸成 else + except 后 break 位置错 | B |
| 5 | _FileInFile.read | 668-697 | 502-531 | 143/130 | 外层 `while size > 0` 降级为 `if size > 0`（`POP_JUMP_BACKWARD_IF_TRUE` 回边整体消失）；`start <= position < stop` 链式比较坍塌（SWAP/COPY/第二 COMPARE 共 7 条蒸发）；内层 break/else 重组 | 循环检测失败 + 链式比较坍塌（多机制） | D/C 未闭合 |
| 6 | TarInfo.create_pax_header | 1024-1080（判定 1060-1068） | 741-775 | 172/171 | 少 1 条 `JUMP_FORWARD`：`elif val_is_float:` 被降级为顺序 `if`（链退化） | elif 链接丢失 | **C** |
| 7 | TarFile.__init__ | 1643-1741（判定 1712-1741） | 1168-1248 | 323/329 | 循环后 `if self.mode in ('a','w','x')` 整块被拖进 `while True` 体内（`JUMP_BACKWARD`/目标偏移全错）+ 2 个多余 RETURN + except 臂 else 融合 | 循环后块归属越界（+A/B 残余） | D（+A/B） |
| 8 | TarFile.gettarinfo | 2004-2084（判定 2045-2058） | 1456-1531 | 307/307 | 仅 1 条边：`574 POP_JUMP_FORWARD_IF_TRUE ->692` vs `->742` | `not <属性> and … and …` 四成员链被拆成嵌套 if，else 挂到内层、外层无 else | **C** |
| 9 | TarFile.list | 2103-2139（判定 2114-2139） | 1532-1563 | 163/153 | `_safe_print("%s/%s" % (a or b, c or d))` 整调用丢失（`LOAD_GLOBAL _safe_print`+FORMAT_VALUE/BUILD_STRING+PRECALL/CALL 共 5 条消失，只剩两个 or 的裸 Expr）；循环尾 `if verbose:` 变裸 `verbose`（`POP_JUMP_FORWARD_IF_FALSE`→`POP_TOP`） | 3.11 把 %-format 优化成 f-string 字节码，该组重建丢调用；块尾条件裸 Expr | E |
| 10 | TarFile.add | 2141-2190 | 1564-1601 | 182/183 | `elif filter is not None`（源为独立 if）+ with 体内/for 体内多余 `return None` + 1 个 NOP | 终结符 if 融合成 elif + 臂尾 Return 注入 | A（+B） |
| 11 | TarFile.next | 2581-2641 | 1923-1980 | 288/279 | InvalidHeaderError/EmptyHeaderError 处理器内 `elif self.offset == 0: raise` 与 raise 的相对顺序被打乱、`break` 插进 except 体、尾部 `if tarinfo is not None: pass` | 异常处理器链重排（跨族） | 未归族 |
| 12 | TarFile._load | 2686-2694 | 2009-2017 | 16/11 | `tarinfo = self.next()` 整体丢失 + 极性反转（`if tarinfo is None`→`if tarinfo`） | while 头语句吞没 + 极性反转 | D |
| 13 | TarFile._check | 2696-2703 | 2018-2027 | 32/32 | 指令全同，仅两条边落点互换 → 因为 `elif` 臂尾多一行 `return None`，把单一出口劈成两个 RETURN 块 | 臂尾 Return 注入 | A |
| 14 | main | 2800-2890 | 2101-2167 | 473/443 | `tar_files = args.create` 与 `with TarFile.open(tar_name, tar_mode) as tf:` 整块丢失（`tf` 降级为全局名）+ 2 处 `else: return None` | 块内 with 语句整体吞没（跨族） | 未归族 |

**判定要点**：14 个单元里 11 个的实差是"1 条边 / 1 条指令 / 3 条收尾指令"级别，属可精确定位的结构性错误；只有 3 个（_FileInFile.read、next、main）是"多指令块蒸发"级。

---

## 2. 候选族与"修复面/风险比"

| 族 | 定义（一句话） | 单元 | 实测闭合 | 修复面 | 异常表 | 循环区 | 与已修族重叠 | 风险 |
|----|----------------|------|----------|--------|--------|--------|--------------|------|
| **A** | 块臂/函数尾被合成 `return None`（tail Return 提升越界） | _check, add（+部分 __init__/main） | **+2** | 只删合成 Return，不改跳转 | 无 | 无 | 与 v160 DEEPRET 共用 Return 发射点，但不同域 | 低（回归面＝所有函数的隐式 return 提升） |
| **B** | `if <return/raise/break>` 之后的语句被吸成 `elif/else`（终结符未切断链） | _Stream.__init__, _Stream._read | **+2** | 链/else 边归属 | 无（只碰 except 臂与 if 结构） | 无 | CHAINGRAFT(v162) 同域残余 | 低-中（if 链构建器全局共享） |
| **C** ★ | 多块条件（链式比较 / BoolOp / `not <属性>`）作为链头或链成员时，链的 else/汇合边归属错位 | itn, create_pax_header, gettarinfo | **+3** | 准入窗（栈深回溯）+ 操作数分组 + 链边归属 三处联动 | **零** | **零** | NOTCOND(v159 窗加 CONTAINS_OP)、NOTMIX(v161)、NOTMIX-HEAD2(v164)、r156 已登记专项轮 | 中（链构建器通用），但三个单元 exc 表逐字节相同 |
| **D** | 循环区边界：循环后块被拖进循环体、while 头语句吞没 | TarFile.__init__, _load | **+2** | 区域归属/循环检测 | 无 | **高**（直接动循环区） | for-iterable 归属(v163) 同带 | 高 |
| **E** | 3.11 的 `%`→f-string 优化字节码（FORMAT_VALUE/BUILD_STRING）组重建时丢调用；块尾条件裸 Expr | list | **+1** | 组重建 + 条件发射 | 无 | 无 | r156 BINPAREN 是渲染层，不同 | 中（组重建影响面宽） |
| **F** | 混合 `not or` 作为循环出口条件 → `if s: if s == NUL: break else: break` 形反转 | _Stream._init_read_gz | **+1** | 同 C 的 BoolOp 边归属，落到 break 体 | 无 | 中 | NOTMIX(v161) 同源 | 中（loop break 体） |
| — | 未归族 | _FileInFile.read（循环降级＋链式比较坍塌）、next（异常处理器链重排）、main（with 块吞没） | 0 | 多机制叠加 | 有 | 高 | — | 高（不建议本轮碰） |

> 说明：实测闭合是在"只还原该族源形、其余保持现状"的累积变体上得到的边际值，因此可直接读作"该族单独做能闭合几个单元"。变体脚本 `mkvar2.py`，产物 `var_A.py` … `var_ABCDEF.py`。

---

## 3. 首选族 C —— 多块条件（链式比较 / BoolOp）在 if/elif 链中的链边归属

### 3.1 三个面（全部实测复现，见 §5 复现清单）

| 面 | 触发形 | 产物错误形 | 单元 |
|----|--------|-----------|------|
| C-a | `elif <简单比较> and <链式比较>:`，链尾有 `else` | `elif <简单比较>:` + 内层 `if <链式比较>: … else: <链的 else>` —— **else 被挂到内层 if** | itn |
| C-b | `if not <链式比较>:` 作为链头，后随 `elif` | 链头正常、`elif` 被降级为顺序 `if`（少 1 条 JUMP_FORWARD） | create_pax_header |
| C-c | `if not <属性加载> and A and B and C:` + `else` | `if not <属性加载>:` + 内层 `if A and B and C: … else: …` —— **整链被拆、else 挂到内层、外层无 else** | gettarinfo |

三面共同点：**参与 if/elif 链的那个测试跨越多个基本块（链式比较的 SWAP/COPY 双比较、BoolOp 短路、`not` 包链）时，链的 else/汇合边被记到了错误的测试块上**——要么记到链内最后一个操作数块（C-a/C-c，于是 else 变成内层 if 的 else），要么记到汇合块（C-b，于是 elif 链接消失）。

### 3.2 为什么现在可行（依赖已落地族）

- v159-NOTCOND 已把 **FALSE 模式 BoolOp 链准入窗**从"只放行简单变量真值测试"扩到含 `CONTAINS_OP`（成员测试形）；v161-NOTMIX / v164-NOTMIX-HEAD2 已处理 **混合链的极性融合**与链首极性残形。也就是说：链启动窗、极性、链首归属这三层都已经就位，**唯一还卡住的是窗内成员集合里缺 COMPARE_OP 链式比较组与 LOAD_ATTR 真值测试**，以及 else 边的归属落点。
- r156 提交信息本身已经把这族登记为专项轮，并给出失败原因：**"itn and 链链式比较成员（走查 argval≠merge 截断——fix156_andcc 半修回退：链吸收但 body→pass/比较分裂，需分析器+AST 侧操作数分组联动，专项轮登记）"**。即：只改分析器会得到 `body→pass`/比较分裂，必须分析器 + AST 侧操作数分组**同轮联动**（本轮三面正好验证：C-a/C-b 需要"条件被整链吸收后由 AST 侧还原成一个 Compare 链"，C-c 需要"链首成员不拆成独立 if"）。
- 三个目标单元的**异常表逐字节相同**（itn 无异常表，另两个 `exc same=True`），**不含循环**，且实差分别只有 1 条跳转边 / 1 条指令 / 1 条跳转边 → 修复后可用"边落点"级断言直接验证。

### 3.3 最小复现建议（已实测，削到 5-6 行）

已生成并**实测复现同一判官失败**（`repro/` 目录，含 .py/.pyc/.out.py）：

1. `repro/c1_itn.py`（C-a，复现 itn）：
```python
def itn_chain(n, digits=8, fmt="GNU"):
    if 0 <= n < 8 ** (digits - 1):
        s = 1
    elif fmt == "GNU" and -256 ** (digits - 1) <= n < 256 ** (digits - 1):
        s = 2
    else:
        raise ValueError("overflow in number field")
    return s
```
→ 判官 `Failure: Different control flow`；产物 `elif fmt == 'GNU': if …: s=2 else: raise`。

2. `repro/c8_head_chain_only.py`（C-b，复现 create_pax_header；比 c2_pax.py 更小）：
```python
def head_chain_only(n):
    if not 0 <= n < 100:
        s = 1
    elif n == 0:
        s = 2
    else:
        raise ValueError("x")
    return s
```
→ `Failure: Different control flow`；产物把 `elif n == 0:` 降级成 `if n == 0:`。

3. `repro/c3b_notand_attr.py`（C-c，复现 gettarinfo；**注意必须用属性加载**，普通形参形不复现）：
```python
class T:
    def gti(self, st, arcname):
        inode = (st.ino, st.dev)
        if not self.deref and st.nlink > 1 and inode in self.inodes and arcname != self.inodes[inode]:
            t = "LNK"
        else:
            t = "REG"
        return t
```
→ `Failure: Different control flow`；产物 `if not self.deref:` 套内层 if，else 挂内层。

**反向对照（实测全部 Equal，用来锁定修复窗口边界）**：
- `repro/c4_simple_elif.py`：`if not a: … elif b: …`（简单条件）→ Equal ⇒ 不是"elif"本身。
- `repro/c6_elif_and_simple.py`：`elif b and c:`（纯简单成员 BoolOp）→ Equal ⇒ 不是"and"本身。
- `repro/c7_elif_chain_only.py`：`elif 0 <= n < 100:`（elif 成员是纯链式比较）→ Equal ⇒ 不是"链式比较"本身。
- `repro/c3_notand.py`：`not deref and …`（首成员是普通形参而非属性）→ Equal ⇒ C-c 的触发点是 `LOAD_ATTR` 真值测试。

### 3.4 风险

- **中**：if/elif 链构建器是所有分支结构共用的，回归面广；但本族三个单元不触及异常表与循环，且可用 4 个反向对照做"窗口不扩大"验证（对照案必须保持 Equal）。
- 注意别把 v159 的 TRUE/FALSE 窗再放宽到 `COMPARE_OP`（r159 提交里明确写了"COMPARE_OP 链式比较/boolop 结果比较回归风险既有注释"）——正确做法是**把 COMPARE_OP 的"链式比较组"（SWAP/COPY + 2×COMPARE_OP + 两个 POP_JUMP 成对）作为一个整体操作数**准入，而不是把单个 COMPARE_OP 放进简单窗。
- 与 A/B 无冲突：C 的三个单元只做条件链，A/B 不碰这三处。

---

## 4. 备选族 A —— 块臂/函数尾的隐式 `return None` 注入

- 单元（实测闭合）：**_check**（32/32 指令全同，只多一行 `return None` 把单一出口劈成两个 RETURN 块）、**add**（`elif` 修正 + 删 with/for 体内两处 `return None` + 3 处 `return None`→`return`）。
- 部分改善：`_Stream.__init__`（7 处臂尾）、`TarFile.__init__`（2 处 + except 臂）、`main`（2 处 `else: return None`）——但这三个还需 B/D/with 族才能闭合。
- 修复面：只删"合成"的尾随 Return；真正 `return`/`return None` 在字节码上都带显式 `RETURN_VALUE`，与"落到汇合块"可区分，判据是"该块是否只是把跳转目标复制成一次 Return"。
- 风险：低（不动跳转、不碰异常表/循环）；但隐式 return 提升是全局路径，需要电池回归（439 案那套）兜底。
- 最小复现建议（已实测）：
  1. `repro/a2_except_arm.py`（15 行，**一个案子同时触发 A 的 2 处臂尾 Return 与 B 的 except-else 融合**，正是 `_Stream.__init__` 骨架）：
```python
class C:
    def __init__(self, ext):
        self.ext = ext
        try:
            if self.ext:
                self.open()
            else:
                self.make()
        except:
            if not self.ext:
                self.close()
            self.closed = True
            raise
```
→ `Failure: Different control flow`；产物在 `if` 两臂各补 `return None`，并把 `self.closed = True` 吸成 `else:`。
  2. 反向对照 `repro/a1_tail_if.py`（函数尾裸 `if x: print(v)` 跟随 `return 0`）→ **Equal**，说明函数尾形态本身不复现，必须落在 try 体的臂尾/except 臂上；削形时别把它当功效案。

---

## 5. 复现与工件清单（全部在 D:\temp\opencode\cl_layout\r165\）

| 文件 | 用途 |
|---|---|
| `tarfile_now.py` | 本轮重新反编译的产物（判官输入） |
| `judge_now.txt` / `judge_now_raw.txt` | 14 单元 + failure message 记录 / 判官原始输出 |
| `u01..u14*.txt` | 14 个单元的"真实源 vs 产物"≤80 行对照窗口（extract.py 生成） |
| `bcdiff2.py` / `vdiff.py` / `bcdiff.py` | 原始 pyc 与（任意版本）产物的逐指令对齐/差分工具 |
| `mkvar2.py` | 族变体生成器（A–F，py_compile 自检；越界/重叠断言） |
| `var_A.py` … `var_ABCDEF.py` | 六族累积变体，判官读数 148/150/153/155/156/157 |
| `repro/` | 11 个削减小例（.py/.pyc/.out.py）：c1/c2/c3/c3b/c4/c5/c6/c7/c8（C 族 3 功效案 + 4 反向对照 + 1 判别案）、a1/a2（A+B 族） |
| `extract.py` | 按 qualname 取真实源与产物窗口 |

## 6. 未闭合的 3 个单元（本轮不建议碰）

- **`_FileInFile.read`**（143→130）：外层 `while size > 0` 被降级为 `if`（循环回边整条消失）＋ `start <= position < stop` 链式比较坍塌＋内层 break/else —— 循环检测 + 链式比较 + break 归属三机制叠加。
- **`TarFile.next`**（288→279）：异常处理器链（InvalidHeaderError / EmptyHeaderError / TruncatedHeaderError / SubsequentHeaderError）内部 `elif self.offset == 0: raise` 的相对顺序被打乱、`break` 插进 except 体、尾 `if tarinfo is not None: pass` —— 动异常表，高风险。
- **`main`**（473→443）：`tar_files = args.create` 与 `with TarFile.open(tar_name, tar_mode) as tf:` 整块蒸发（`tf` 降级为全局 `LOAD_GLOBAL`）—— 块内 with 归属，与 v158 RETFIN（try+finally 内联）相邻但不同域，需单独侦察。
