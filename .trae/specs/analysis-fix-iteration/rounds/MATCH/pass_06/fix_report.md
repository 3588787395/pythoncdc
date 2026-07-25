# Pass 6 MATCH 修复报告

## 修复内容

### Fix 1: 同步 Pass5-MATCH 标记中过时的 `except Exception: pass` 行号引用

**问题位置**：`/workspace/core/cfg/region_ast_generator.py:15618-15627`（`_generate_match` 内 Pass5-MATCH 标记注释段）

**问题根因**（与 Pass5-WITH 同型行号漂移）：
Pass5-MATCH 在标记 `except Exception: pass` 静默吞异常反模式时，写入：
```
# [Pass5-MATCH] 已知反模式（Pass 2 已登记、Pass 4 fix_report
# §未完成项 4 引用 L15531 已过时——经 Pass 4 修改行号已下移至
# L15596）：`except Exception: pass` 静默吞异常...
```

其中 `L15596` 是 Pass5-MATCH 写入时的 `except Exception:` 行号快照。经 Pass6-IF
（在 L11952 添加 [Pass6-IF] 注释段约 12 行）+ Pass6-LOOP（在 L4197 重构 docstring
约 5 行）上游修改后，`except Exception:` 已下移至 Pass5-MATCH 标记下方紧邻位置。

Pass5-MATCH 标记中的 L15596 引用与实际不符，误导读者。

**修复策略**（与 Pass5-WITH 同型——仅注释文本同步）：
保留原 Pass5-MATCH 注释文本不变（历史追溯用），追加 `[Pass6-MATCH]` 段落，说明：
1. Pass 5 写入后经 Pass6-IF / Pass6-LOOP 上游修改使行号再次下移
2. **不再引用具体行号**——改为「现实际位置见紧邻的 `except Exception:` 行」
   （避免递归漂移：本注释段自身会改变行号）
3. 原 Pass 5 引用 L15596 为 Pass 5 写入时的快照，已过时
4. 行号漂移原因：region_ast_generator.py 顶部 Pass6-IF 添加 [Pass6-IF] 注释段
   + Pass6-LOOP 重构 docstring
5. 验证方法：grep `except Exception:` 在 _generate_match 内可重新定位
   （紧邻本注释段下方的 `except Exception:` 即为该反模式位置）
6. 后续 Pass 若实施「save-mutate-restore 统一到识别期」可一并消除此反模式与
   行号引用漂移源

**为什么不引用具体行号**（与 Pass5-MATCH / Pass5-WITH 不同）：
Pass5-MATCH / Pass5-WITH 都引用了具体行号，但每轮上游修改都会使行号继续漂移，
形成「行号引用→漂移→再同步→再漂移」的递归问题。本轮 Pass6-MATCH 改用「紧邻
本注释段下方的 `except Exception:`」相对位置描述，不再依赖绝对行号，从根因上
消除漂移源。

控制流不变，仅注释文本同步。

## 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```
**结果**：退出码 0，输出 `COMPILE_OK`。

## 回归测试

```
timeout 290 python .trae/specs/analysis-fix-iteration/run_region_tests.py MATCH
```
**结果**：`79 0 0 79 2.1 MATCH files=80` —— 与基线一致（79 passed, 0 failed, 0 errors）。无退化。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变（仅添加注释） |
| 测试文件修改 | 未修改任何测试文件 |
| 过时注释行号引用 | **已同步**（追加 [Pass6-MATCH] 段落，改用相对位置描述避免递归漂移） |

## 未完成项

1. **`except Exception: pass` 静默吞异常消除**（Pass 5 已标记、本轮同步行号引用）：
   控制流变更，需评估 `nested_found` 兜底语义后改写为有针对性的 except + log。
2. **`_detect_undetected_wildcard_match` 反模式未消除**（Pass 3 已标记）：待
   region_analyzer 阶段统一识别通配符 match 后删除本方法及 3 处调用点
   （L322/L582/L608，本轮 grep 确认行号未漂移）。
3. **`_region_overlaps_with_ternary` 反向过滤**（Pass 1 已登记）：未处理。
4. **`_identify_match_regions` 越权捷径与 Phase 2.5 职责合并**（Pass 1 已登记）：未处理。
5. **`_generate_match` 内 ~200 行字符串字面量**（Pass 2 评估未采用）：技术上属冗余
   no-op 表达式，但内容为意图性文档，本轮保留。

## 文件清单

- `/workspace/core/cfg/region_ast_generator.py`（Fix 1：`_generate_match` 内 Pass5-MATCH 标记追加 [Pass6-MATCH] 同步段落，改用相对位置描述避免递归漂移）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/MATCH/pass_06/fix_report.md`（本报告）
