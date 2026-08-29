# Round 05 — G4 家族修复报告（海象赋值 value 位置的下标/属性目标）

## 1. 目标

修复 G4 家族缺陷：`target = (r := value)` 形式中海象运算符位于赋值 **value 位置**、
目标为下标（`d[k]`）或属性（`obj.x`）的语句被错误反编译（典型症状：`r = make(); 0[None] = f`）。

修复原则（全程遵守）：
- 区域归约：每块唯一归属、嵌套即抽象节点、入口引用语义。
- 禁止 anti-pattern 前缀（`_fix_`/`_patch_`/`_hack_`）与跨区启发式、硬编码深度。
- 反编译产物与原 pyc **字节码完全等价**（`(opname, argval)` 序列一致）为唯一正确性判据。

## 2. 关键发现

1. **value 位置海象 ≡ 链式赋值（逐字节等价）**：在 CPython 3.11.7 中，
   `d[k] = (r := v)` 与 `r = d[k] = v` 编译出的字节码**完全一致**；
   `d[f()] = (r := make())` 与 `r = d[f()] = make()` 同样**逐字节一致**。
   因此复现集接受 byte-identical 的链式形式，无需强制 NamedExpr 形态。

2. **r01 已由既有 W16 混合链逻辑正确处理**：`_generate_block_statements_body` 内的
   W16 handler（`_mixed_chain_result`）对简单值（`v`、`k` 为 `LOAD_FAST`）能正确产出
   `r = d[k] = v`。r05/r07 失败并非缺少 walrus 处理，而是 W16 的**操作数分组**函数
   `_w16_split_value_groups` 无法把下标/属性的操作数正确拆成「容器组 + 键组」。

3. **根因定位（实证 trace）**：`_chain_instrs` 在派生时已剥离 `PUSH_NULL`。
   - r05 `d[f()]` 的下标 key 序列为 `[LOAD_GLOBAL f, PRECALL, CALL]`，旧分组函数遇
     `PRECALL/CALL` 直接 `return None` → W16 失效，回退到通用循环把 `make()` 与
     `d[f()]` 拆断 → `r = make(); 0[None] = f`。
   - r07 `a[b][c]` 的 obj 序列为 `[LOAD_FAST a, LOAD_FAST b, BINARY_SUBSCR]`，
     旧函数把 `LOAD_FAST b` 误判为新值组 → 分组数错误 → W16 失效。

## 3. 修复

### 3.1 `_w16_split_value_groups` 重写为「操作数合并」线性扫描（核心修复，本回合）
旧实现用「每条 LOAD 开启新值组」的朴素模型，无法表达：
- 调用表达式（多 LOAD 合并为 1 个值）；
- 下标合并（`a[b]`、`a[b][c]` 整体为 1 个值）。

新实现按栈值操作数分类扫描，使每个分组恰好对应 STORE 的一个操作数：
- **值起始**：`LOAD_*` / `BUILD_*` → 开启新分组；
- **中缀延续**：`LOAD_ATTR` / `LOAD_METHOD` / `PRECALL` / `UNARY_*` / `GET_ITER` /
  `FORMAT_VALUE` 等 → 依附当前分组；
- **二元合并**：`BINARY_SUBSCR` / `BINARY_SLICE` / `BINARY_OP` / `COMPARE_OP` /
  `CONTAINS_OP` / `IS_OP` → 消费栈顶 2 个分组并合并为 1 个（→ 嵌套下标、二元运算）；
- **调用合并**：`CALL` / `CALL_NO_KW` / `CALL_FUNCTION_EX` / `CALL_INTRINSIC_*` →
  消费 `(argc + 1)` 个分组（可调用对象 + 实参）并合并为 1 个（→ 下标/属性键中的 `f()`、`obj.m()`）。

W16 handler 据此把 `d[f()]`、`a[b][c]` 等正确拆成 2 个分组，产出 byte-identical 的
`r = d[f()] = make()` / `r = a[b][c] = make()`。

### 3.2 既有 walrus helper（上回合已落地，本回合保留）
- `_detect_walrus_prefix` / `_build_walrus_assign`：通用 walrus 前缀检测与 NamedExpr 重建。
- `_generate_handler_body_statements` 的 STORE_FAST 分支：处理 except/finally handler 体内的
  walrus-in-value（r10 用例），产出链式或 NamedExpr 形式。

## 4. 验证

- **G4 最小复现集 12/12 PASS**（字节码完全等价）：
  r01 简单下标、r02 下标+调用值、r03 简单属性、r04 属性+调用值、
  r05 下标计算索引（`d[f()]`）、r06 属性容器下标（`self.cache[k]`）、
  r07 嵌套下标（`a[b][c]`）、r08 二元值、r09 方法值、r10 except handler、
  r11 多级属性（`o.a.b`）、r12 常量值。
- **真实 pyc 实证修复（`fly_api/base.pyc`，Round 05 主目标）**：
  - 修复前（基线代码）`get_instance` 中 G4 行被错误反编译为：
    ```python
    store_class[None] = self.instance_dict        # 错误：下标/值操作数错位
    ```
  - 修复后（本回合 W16 修复）正确还原为字节码完全等价形式：
    ```python
    self.instance_dict[store_class.__name__] = (r := store_class())
    ```
  即之前若按反编译产物重编译，会因 `store_class[None]` 与原始 `self.instance_dict[...]=...`
  字节码不一致而失败；修复后重编译 `(opname, argval)` 序列与原始 pyc 逐条一致。
- **全量回归**：`pyc_batch_verify.py batch --round 5` 覆盖全部 402 个索引 pyc：
  - 总 402，验证 402，**失败 0**；ok 304 / partial 98（与本回合修复前相比，ok/partial/failed 计数完全不变，零回归）；
  - 累计函数匹配率 94.12%（matched 4846 / total 5149）。
  - 基线对照（`--round 0` 仅复验既有 304 个 ok pyc，得 99.96% 匹配）与全量 `--round 5` 口径不同，不可直接按函数数比较；但两者 **failed 均为 0、ok 计数均为 304**，可确认本回合修复未引入任何回退。
  - 对全量 `*OK.py` 扫描，已无 `X[None] =` 类错位残留（修复前 `fly_api/base.pyc` 即输出 `store_class[None] = self.instance_dict`）。

## 5. 反模式自检

- 无 `_fix_`/`_patch_`/`_hack_` 前缀新增方法或分支。
- 未引入跨区启发式或硬编码深度；修复完全基于字节码操作数结构。
- 调试桩（`G4DBG` 打印）已全部移除，仅保留结构性 walrus 处理。
