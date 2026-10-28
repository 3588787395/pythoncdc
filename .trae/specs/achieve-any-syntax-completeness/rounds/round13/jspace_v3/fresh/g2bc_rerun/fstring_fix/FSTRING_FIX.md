# Round13 f-string 语法族根因修复（REAL46-004）

## 缺陷与根因

REAL46-004 反编译 enum.py 后，产物在 line 1497 附近生成：

```python
failed.append(f'{name!r} member mismatch:\n      {"""
      """.join(failed_member)!s}')
```

单引号定界的 f-string，其**表达式片段**（`{...}` 内）
`"""\n      """.join(failed_member)` 含**真实换行**。CPython 3.11（PEP 701
之前）f-string 先被词法层整体扫描为一个 STRING token：单字符定界下表达式
片段含真实换行必然 `SyntaxError: unterminated string literal`。

这不是单点笔误，而是**定界符选择算法的族级缺陷**：`_generate_joined_str`
（AST 路径）与 `_generate_joined_str_from_dict`（dict 路径）只按表达式片段
的引号字符选 `'/"/'''`，**未考虑真实换行**（换行强制三引号定界）、**未考虑
反斜杠**（任何定界都非法）、**未考虑三引号定界与表达式内完整三连序列的冲突**。

## CPython 3.11.7 实测定界边界

探针 `fstr_probe3_311.py` / `fstr_probe4_311.py`（归档于 `fstring_fix/`）：

| 场景 | 结果 |
|---|---|
| 表达式含换行 + 单引号定界 | SyntaxError（REAL46-004 现状） |
| 表达式含换行 + `'''` 定界 | **OK**（P17，REAL46-004 精确形态 eval 正确） |
| 表达式含反斜杠（任何定界） | SyntaxError `f-string expression part cannot include a backslash`（P9b/P9c） |
| `'''` 定界 + 表达式含 `'''` 三连 | SyntaxError（P7/P14） |
| `"""` 定界 + 表达式含 `'''` | OK（P15b） |
| spec 区反斜杠 | OK（P8，合法，反斜杠扫描须排除 spec 区） |
| 三引号定界，字面尾部裸引号 | SyntaxError（P18b）；转义后 OK（P18） |

## 修复（两层，窄范围族级）

改动仅在 `core/cfg/code_generator.py`：

1. **`_select_fstring_delimiter(expr_texts)`**（新增，两条路径共用）：
   - 表达式片段含反斜杠 → 任何定界都非法 → 返回 `None`（走 Tier 2）。
   - 无换行：沿用旧优先级 `'`→`"`（逐字节一致）。
   - 含换行或单双引号同时出现 → 三引号：`'''`（若表达式不含 `'''`）→
     `"""`（若不含 `"""`）→ 都冲突返回 `None`（Tier 2）。
2. **`_escape_fstring_literal`**（新增）：单/双引号定界转义与旧码逐字节
   一致；三引号定界转义**全部**同类引号，彻底消除字面尾部/跨片段引号与闭合
   定界符粘连出三连（P18b）。
3. **Tier 2 回退 `_build_fstring_concat_fallback`**（新增）：无有效定界符时
   输出带括号的 `('lit' + format(expr, 'spec') + ...)`，语义等价
   （`f'{x!s:spec}' ≡ format(str(x), 'spec')`），恒可编译。触发条件（表达式
   含反斜杠、或两种三引号序列都冲突）下旧产物必为 SyntaxError，**无回归面**。

普通 f-string 路径（无换行、无反斜杠、无三连冲突）逐字节不变。

## 验证

- **REAL46-004**：重新反编译，产物**完全可编译**（`FULL_COMPILE_OK`）。
  f-string 现为 `f'''{name!r} member mismatch:\n      {"""\n      """.join(failed_member)!s}'''`
  —— `'''` 定界 + 字面 `\n` 转义 + 表达式 `"""` 三双引号含真实换行，eval
  正确产出 `SPAM member mismatch:\n      m1\n      m2`。
  语义维度从 `LOAD + R0 + 58×R5` 变为 `LOAD + R0 + 58×R5 + R2/R3/R4`，仍
  DIFFERENT —— 但剩余 `LOAD`/`R0` 是**另一个独立缺陷**：产品 exec 时报
  `UnboundLocalError: use_args`（line 725 `_find_new_`，enum 元类中条件赋值
  的变量被无条件 return 引用），属 CFG **控制流**反编译问题，与 f-string
  语法族无关。f-string SyntaxError（本族目标缺陷）已消除。
- **dict 路径探针** `fstr_fix_probe.py`（T1–T8）、**AST 路径探针**
  `fstr_fix_probe2.py`（A1–A5）：全部 `COMPILE_OK`，覆盖换行、反斜杠
  （Tier 2）、单双引号、三连冲突、spec、字面尾部引号。
- **CORPUS402-0226**（G2b 已知 DIFF）：仍 DIFFERENT，仅 `R7`（2 处），
  产物哈希不变（`4D30C2D2…`），**无回归**（该案例非 f-string 语法错）。
- **G5 回归**（core/cfg 已改，全量复跑）：402 八分片 **6617/6617**、
  small34 **1568/1568**、quotation **153/153**、pytest
  `2 failed, 282 passed, 2 xpassed`（既有冻结对）、IV.2 `IMPORT_OK`/
  `COMPILE_OK`/`G3=0`。功能读数与 rr-v5r77 基线逐项一致，**无回归**。

## 诚实边界

- 本修复只针对 **f-string 语法族**。REAL46-004 仍有第二个独立的 CFG 控制流
  缺陷（`use_args` UnboundLocalError），使该条目仍 DIFFERENT。
- G5 批量比较的是冻结的 `*OK.py` 产品（不重新生成），因此不体现本修复的
  正向增益；真正检验当前树的是 pytest 7 套件 + IV.2（均绿）。
- 不宣称 G1/G2b/G2c/G3/G4/G6 通过。G1 仍 `1180/1556`（376 阻断）；G4 仍
  FAIL；G2b/G2c 环境受限。
- `gate_g5()` 在 core/cfg 未提交时按设计降为 INCONCLUSIVE；功能读数已全绿，
  提交后即 PASS。

## 证据哈希

| 文件 | SHA256 |
|---|---|
| `semantic_46_fix.json` | `E51F01C0B12A07D36A2C3B48082E309E0FA26EE8A84D8271FAA3C8FDCA1BA74B` |
| `semantic_402_0226_fix.json` | `424E1ADD6D2ACB89B83C7C534E6A36C9B05A83A1E14D2CA50DF4795BC72CF8FD` |
| `products_probe_fix/REAL46-004.py` | `C057D79B63E1B5E4D376FCF17676941D3FC7309142CA5B8D2C691EE5F9BA3036` |
| `products_probe_fix/CORPUS402-0226.py` | `4D30C2D2C461F239B31D042F4DCD75E020B3E9D8CC4220F899375035446736B3` |

G5 证据：`fresh/g5_rerun/out/g5_regression_current.json`（本轮复跑覆盖，功能读数同基线）。
