#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""J 空间 v3 备料器 / Judgment-space v3 preparation (Task 5.5).

把 J v2 清单逐条推进到「可判定」状态。J v2 的两处债务在本沙箱内都可修复：

  1. `pyc` 缺失（清单里 `pyc_present=true` 是历史机器的读数，本树内 1556 条
     的 `pyc` 路径**无一存在**）。本脚本对缺失者按 `p_j` 源以
     `PycInvalidationMode.UNCHECKED_HASH` 重新编译（内容寻址，可重生成：
     同源两次运行产出逐字节相同的 pyc 与 sha256）。
  2. `input_model.calls` 为空（1107 条）。Task 5.3 只派生「零参/全默认」顶层
     可调用对象；本脚本把派生面扩展到**必需位置参数**：按注解 > 参数名 > 常量
     的确定性优先级合成实参字面量，生成 `f(<seed>, ...)` 形式的调用表达式。

纪律：
  * 派生只读 `p_j` 源 AST（结构事实），不读 J 期望标签、不读 verdict；
  * 实参种子是**固定字面量表**（见 `ANNOTATION_SEEDS` / `NAME_SEEDS`），
    不依赖被测代码的行为，也不按条目 id 特判；
  * 生成不了的条目**不伪造** calls：保留空表并在 `derivation` 里写原因；
  * 原始 `pyc` 若存在则**原样保留**，只在缺失时重编译并在记录里标明。

用法：
    python -X utf8 tools/completeness/jspace_v3_prepare.py \
        --space .trae/specs/attack-completeness-claims/rounds/round9/judgment_space.json \
        --out   .trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/judgment_space_v3.json \
        --pyc-dir .trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/pyc \
        --report  .trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/prepare_report.json
"""

from __future__ import annotations

import argparse
import ast
import collections
import hashlib
import json
import os
import py_compile
import sys

TOOL_VERSION = "1.0.0"
MAX_CALLS_PER_ENTRY = 6
SKIP_NAMES = frozenset({"input", "breakpoint", "exit", "quit"})

# 允许派生调用的降级原因白名单（`excluded` 条目的原由子串）。
# 只放「探针/合成源缺零参入口」一族：这些源是本仓为判定空间写的测试探针，
# 调用它们只影响临时目录内的状态。
DERIVABLE_REASONS = ("no zero-arg/defaulted top-level callable",)

# 禁止派生调用的原因（安全闸）：真实业务包模块的顶层可调用对象可能带进程/
# 网络/交易副作用，且其依赖闭包（six/jsonpickle 等）在本沙箱不完整 ⇒ 既无法
# 保证可执行，也无法保证副作用收敛。这些条目维持 module_only，不伪造 calls。
UNSAFE_REASONS = ("real-package module",)

# 注解 → 实参字面量（字符串形式，直接拼进调用表达式）
ANNOTATION_SEEDS = {
    "int": "1",
    "float": "1.0",
    "complex": "1j",
    "bool": "False",
    "str": "'x'",
    "bytes": "b'x'",
    "list": "[]",
    "dict": "{}",
    "tuple": "()",
    "set": "set()",
    "frozenset": "frozenset()",
    "None": "None",
    "Any": "1",
}

# 参数名 → 实参字面量（注解缺失/不可映射时的回落，按子串匹配，长键优先）
NAME_SEEDS = (
    ("argv", "[]"),
    ("args", "[]"),
    ("kwargs", "{}"),
    ("path", "'x'"),
    ("filename", "'x'"),
    ("file", "'x'"),
    ("name", "'x'"),
    ("text", "'x'"),
    ("message", "'x'"),
    ("msg", "'x'"),
    ("data", "[]"),
    # 序列型形参给**非空**字面量：`[]` 会让循环体一次都不执行，C4 的 R1–R6
    # 全被空输入掩盖（实测 `/tmp/mini` 族与 B142 探针只报 R7）。`[0, 1, -1]`
    # 同时覆盖正/零/负三支，且两侧用同一实参，比较仍然公平。
    ("rows", "[0, 1, -1]"),
    ("items", "[0, 1, -1]"),
    ("values", "[0, 1, -1]"),
    ("lst", "[0, 1, -1]"),
    ("seq", "[0, 1, -1]"),
    ("mapping", "{}"),
    ("dict", "{}"),
    ("count", "1"),
    ("size", "1"),
    ("num", "1"),
    ("length", "1"),
    ("index", "0"),
    ("idx", "0"),
    ("i", "2"),
    ("j", "2"),
    ("k", "2"),
    # `n` 只作默认上界：取 1 使 `while n:` 一类条件循环在探针里必然收敛
    # （取 2 时 `_run(v_while_cond_nest)` 一族在 C4 里整片超时，见
    # rounds/round13/jspace_v3 的 INCONCLUSIVE 读数）。
    ("n", "1"),
    ("x", "1"),
    ("y", "1"),
    ("flag", "False"),
    ("verbose", "False"),
    ("ok", "False"),
)
DEFAULT_SEED = "1"


def load(path):
    """读 JSON（容忍 UTF-8 BOM）。"""
    with open(path, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def canonical(data):
    """稳定序列化：G4/G1 的哈希链只允许键序无关的规范化文本。"""
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(data):
    """规范化文本的 SHA256（用于 J v2 溯源，不参与判定）。"""
    return hashlib.sha256(canonical(data).encode("utf-8")).hexdigest()


def sha256_file(path):
    """文件字节 SHA256；不可读返回 None。"""
    try:
        with open(path, "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()
    except OSError:
        return None


def annotation_seed(node):
    """把一个注解 AST 映射为实参字面量；不可映射返回 None。

    只认名字/属性尾名/下标外层（`Optional[X]`、`list[int]` 取外层名），
    以及 `X | None` 取左支。任何其它形态一律 None（不猜）。
    """
    if node is None:
        return None
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return annotation_seed(node.left)
    if isinstance(node, ast.Subscript):
        return annotation_seed(node.value)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, str):
            return ANNOTATION_SEEDS.get(node.value)
        if node.value is None:
            return "None"
        return repr(node.value)
    if isinstance(node, ast.Name):
        return ANNOTATION_SEEDS.get(node.id)
    if isinstance(node, ast.Attribute):
        return ANNOTATION_SEEDS.get(node.attr)
    return None


def name_seed(name):
    """按参数名子串匹配固定种子表（长键优先 ⇒ 结果与实现顺序无关）。"""
    low = (name or "").lower()
    for key, seed in sorted(NAME_SEEDS, key=lambda kv: -len(kv[0])):
        if key in low:
            return seed
    return DEFAULT_SEED


def _walk_local(node):
    """按源码序产出 `node` 子树内的节点，**不进入**嵌套 def/class/lambda。

    调用可行性只取决于被调用函数自身作用域：嵌套函数里的死循环/break 不会
    影响外层调用的收敛性，反之亦然。所以这里刻意做作用域内下行。
    """
    stack = [node]
    while stack:
        cur = stack.pop()
        yield cur
        children = [child for child in ast.iter_child_nodes(cur)
                    if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef,
                                              ast.ClassDef, ast.Lambda))]
        stack.extend(reversed(children))


def _truthy_constant(node):
    """`while 1:` / `while True:` 一类常量真条件。"""
    return isinstance(node, ast.Constant) and bool(node.value)


def _loop_can_exit(loop):
    """循环体内是否出现 `break`/`return`/`raise`（作用域内，源序无关）。"""
    return any(isinstance(item, (ast.Break, ast.Return, ast.Raise))
               for item in _walk_local(loop))


def _loop_never_terminates(loop):
    """`while <常量真>:` 且体内无任何出口 ⇒ 该循环不可收敛（结构判定）。

    这是**静态可判定**的一类：常量真条件不会被体改写，体内又没有
    break/return/raise，则循环必然无限。探针对它做任何实参都只会超时。
    """
    return _truthy_constant(loop.test) and not _loop_can_exit(loop)


def _assigned_names(node):
    """`node` 子树（作用域内）被写入的名字集合（赋值/增量赋值/for 目标）。"""
    names = set()
    for item in _walk_local(node):
        if isinstance(item, ast.Name) and isinstance(item.ctx, (ast.Store, ast.Del)):
            names.add(item.id)
    return names


def _loop_has_self_progress(loop):
    """循环条件是否引用体内被改写的名字（即有「体内进度」驱动收敛）。

    `while n: n -= 1` 有进度（test 引用 n，体写 n）；`while <只读 a/b/c/d>:
    n -= 1` 没有进度（条件与体内改写无关）⇒ 实参选择无法靠「递减到 0」
    收敛，必须靠把条件本身取成假值。
    """
    if _truthy_constant(loop.test):
        return True
    test_names = {item.id for item in _walk_local(loop.test) if isinstance(item, ast.Name)}
    body_names = set()
    for stmt in loop.body:
        body_names |= _assigned_names(stmt)
    return bool(test_names & body_names)


def _local_loops(node):
    """`node` 自身作用域内的 `while` 节点（源序）。"""
    return [item for item in _walk_local(node) if isinstance(item, ast.While)]


def _skip_non_terminating(node):
    """函数不可安全调用：自身作用域内存在常量真且无出口的循环。"""
    return any(_loop_never_terminates(loop) for loop in _local_loops(node))


def _needs_falsy_profile(node):
    """函数内存在「无体内进度」的循环 ⇒ 需要一份全零实参变体。

    B240 根因：`while (a if f1 else b) if (c if f2 else d) else 0: n -= 1`
    的条件只读 a/b/c/d/f1/f2，与体内改写的 n 无关；`n=1` 只会让 n 递减到
    负数而不影响条件 ⇒ 全一实参下永久循环、C4 超时。全零实参把 IfExp 条件取成
    假值，循环立即退出，从而把该条目的 R1–R6 行真正执行到。
    """
    return any(not _loop_has_self_progress(loop) for loop in _local_loops(node))


# 全零变体：把种子表里的「1/2」类数值降为 0，其余（''、[]、{}、False）原样。
FALSY_SEEDS = {"1": "0", "1.0": "0.0", "1j": "0j", "2": "0"}


def param_seed(arg, profile="default"):
    """单个参数的实参字面量：注解 > 参数名 > 默认；`falsy` 变体取零值。"""
    seed = annotation_seed(arg.annotation) or name_seed(arg.arg)
    if profile == "falsy":
        return FALSY_SEEDS.get(seed, seed)
    return seed


def function_calls(node, qualname="", profile="default"):
    """为一个函数/方法生成调用表达式；必需参数按种子表合成。

    返回 `[call_expr, ...]`（可能为空：异步函数不做派生——`eval` 里无法 await，
    返回的协程对象也无法规范化比较）。`*args`/`**kwargs` 不展开。
    `profile="falsy"` 生成全零实参变体（见 `_needs_falsy_profile`）。
    """
    if isinstance(node, ast.AsyncFunctionDef):
        return []
    spec = node.args
    positional = list(getattr(spec, "posonlyargs", [])) + list(spec.args)
    required = len(positional) - len(spec.defaults)
    if required < 0:
        required = 0
    seeds = [param_seed(arg, profile) for arg in positional[:required]]
    kwonly = list(spec.kwonlyargs)
    kw_defaults = list(spec.kw_defaults)
    tail = []
    for arg, default in zip(kwonly, kw_defaults):
        if default is None:
            tail.append("%s=%s" % (arg.arg, param_seed(arg, profile)))
    args = seeds + tail
    return ["%s(%s)" % (qualname + node.name, ", ".join(args))]


def class_calls(node):
    """为一个类生成构造调用：`__init__` 的必需参数按种子表合成。"""
    init = None
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name in ("__init__", "__post_init__"):
            init = item
            break
    if init is None or isinstance(init, ast.AsyncFunctionDef):
        return ["%s()" % node.name]
    spec = init.args
    positional = list(getattr(spec, "posonlyargs", [])) + list(spec.args)
    if positional and positional[0].arg in ("self", "cls"):
        positional = positional[1:]
    required = len(positional) - len(spec.defaults)
    if required < 0:
        required = 0
    seeds = [param_seed(arg) for arg in positional[:required]]
    return ["%s(%s)" % (node.name, ", ".join(seeds))]


def _non_terminating_callables(tree):
    """模块内不可安全调用的顶层可调用对象名（含 `Cls.method` / 构造器）。

    只收集**静态可判定**的一类：`while <常量真>:` 且体内无 break/return/raise。
    J v2 已有的 calls 里若出现这些名字，也必须剔除——它们对任何实参都不返回。
    """
    names = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and _skip_non_terminating(node):
            names.add(node.name)
        elif isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and _skip_non_terminating(item):
                    names.add("%s.%s" % (node.name, item.name))
                    if item.name == "__init__":
                        names.add(node.name)
    return names


def _call_prefix(expr):
    """调用表达式被调对象前缀：`f(a)` → `f`，`C.m(a)` → `C.m`。"""
    return (expr or "").split("(", 1)[0].strip()


def derive_calls(tree):
    """从模块 AST 派生**顶层**可调用对象的调用表达式（源序，去重，限流）。

    只取模块顶层 `def`/`async def`/`class`（以及类体内直接定义的普通方法：
    以 `Cls.method(...)` 形式，用于没有 `__init__` 但方法可调用的类）。
    跳过装饰器链里出现 `static`/`property` 之外无法判定形态的对象属于过度设计，
    本函数不做该判定——装饰器只影响调用可行性，异常由 C4 的 R6 记录。

    终态纪律（B240）：
      * 自身作用域内有「常量真 + 无出口」循环的函数**不派生调用**——这类
        函数对任何实参都不会返回，派生只会把整条记录钉成超时；
      * 自身作用域内有「无体内进度」循环的函数（条件不引用体内改写名）：
        全一实参必然复现死循环（实测 `v_while_cond_nest(1,...)` 3 秒即挂），
        而这类探针的测试表达式只读常量实参，没有任何实参能让它「先真后假」。
        故对这类函数**只派生全零实参变体**：条件取假、循环不进入、函数返回，
        使 C1–C5 至少能judge到该函数的非循环路径；
      * 变体追加在常规模板之后，不挤掉常规调用（限流只约束常规面）。

    返回 `(calls, notes)`。
    """
    calls = []
    variants = []
    skipped = []
    falsy = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if isinstance(node, ast.AsyncFunctionDef):
                calls.extend(function_calls(node))
                continue
            if _skip_non_terminating(node):
                skipped.append(node.name)
                continue
            if _needs_falsy_profile(node):
                # 全一实参对本函数是死循环，只保留全零变体（见 docstring）。
                variants.extend(function_calls(node, profile="falsy"))
                falsy.append(node.name)
                continue
            calls.extend(function_calls(node))
        elif isinstance(node, ast.ClassDef):
            calls.extend(class_calls(node))
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name != "__init__":
                    if not isinstance(item, ast.AsyncFunctionDef) and _skip_non_terminating(item):
                        skipped.append("%s.%s" % (node.name, item.name))
                        continue
                    if any(isinstance(d, ast.Name) and d.id in ("staticmethod", "classmethod", "property")
                           for d in item.decorator_list):
                        calls.extend(function_calls(item, qualname=node.name + "."))
    out = []
    for expr in calls:
        if expr.split("(", 1)[0].strip() in SKIP_NAMES:
            continue
        if expr not in out:
            out.append(expr)
    out = out[:MAX_CALLS_PER_ENTRY]
    for expr in variants:
        if expr not in out:
            out.append(expr)
    notes = {"skipped_non_terminating": skipped, "falsy_variants": falsy}
    return out, notes


def compile_pyc(source, target):
    """按 `UNCHECKED_HASH` 失效模式编译 `source` → `target`（内容寻址，可重生成）。"""
    os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
    py_compile.compile(source, cfile=target, doraise=True,
                       invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH)
    return sha256_file(target)


def prepare_entry(entry, pyc_dir):
    """把一条 J v2 记录推进为 J v3 记录；返回 (record, stat_key)。"""
    record = dict(entry)
    record["j_schema_version"] = "v3"
    source = entry.get("p_j") or ""
    stats = {"pyc_regenerated": 0, "pyc_kept": 0, "pyc_failed": 0,
             "calls_derived": 0, "calls_kept": 0, "calls_empty": 0}
    # ---- pyc：存在则保留，缺失则按 p_j 重编译 ----
    old_pyc = entry.get("pyc") or ""
    if old_pyc and os.path.exists(old_pyc):
        record["pyc"] = old_pyc
        record["pyc_sha256"] = sha256_file(old_pyc)
        record["pyc_provenance"] = "existing"
        stats["pyc_kept"] = 1
    else:
        eid = str(entry.get("id") or "entry").replace("/", "_")
        target = os.path.join(pyc_dir, eid + ".pyc")
        try:
            sha = compile_pyc(source, target)
        except (OSError, SyntaxError, ValueError) as exc:
            record["pyc"] = None
            record["pyc_sha256"] = None
            record["pyc_present"] = False
            record["pyc_provenance"] = "compile_failed: %s: %s" % (type(exc).__name__, exc)
            stats["pyc_failed"] = 1
            sha = None
        if sha:
            record["pyc"] = target
            record["pyc_sha256"] = sha
            record["pyc_present"] = True
            record["pyc_provenance"] = "py_compile UNCHECKED_HASH from p_j (python %s)" % sys.version.split()[0]
            stats["pyc_regenerated"] = 1
    # ---- calls：已有则保留，空则按 AST 派生 ----
    model = dict(entry.get("input_model") or {})
    existing = [c for c in (model.get("calls") or []) if isinstance(c, str) and c.strip()]
    if existing:
        # J v2 的 calls 是历史读数，可能含「常量真且无出口」循环的函数（不返回）。
        # 本沙箱内这类调用只会把整条记录钉成 INCONCLUSIVE，故按同一静态判据剔除。
        kept = existing
        dropped = []
        try:
            tree = ast.parse(open(source, "r", encoding="utf-8-sig").read())
        except (OSError, SyntaxError):
            tree = None
        if tree is not None:
            bad = _non_terminating_callables(tree)
            if bad:
                kept = [c for c in existing if _call_prefix(c) not in bad]
                dropped = [c for c in existing if _call_prefix(c) in bad]
        if dropped:
            model["calls"] = kept
            record["call_static"] = {"dropped_non_terminating_calls": dropped}
            stats["calls_filtered"] = 1
        record["input_model"] = model
        stats["calls_kept"] = 1
        record["derivation"] = "kept from v2"
    else:
        why = None
        calls = []
        notes = {}
        reasons = " ".join(str(x) for x in (entry.get("excluded") or []))
        unsafe = [tag for tag in UNSAFE_REASONS if tag in reasons]
        derivable = any(tag in reasons for tag in DERIVABLE_REASONS)
        if unsafe:
            # 安全闸优先：真实业务包模块一律不派生（见 UNSAFE_REASONS 注释）。
            why = "unsafe_host_module: %s" % unsafe[0]
        elif not derivable:
            why = "reason_not_in_derivable_allowlist"
        tree = None
        if why is None:
            try:
                tree = ast.parse(open(source, "r", encoding="utf-8-sig").read())
            except (OSError, SyntaxError) as exc:
                why = "source_unparsable: %s: %s" % (type(exc).__name__, exc)
        if tree is not None:
            calls, notes = derive_calls(tree)
            if not calls:
                why = "no_top_level_callable_with_constructible_arguments"
        model["kind"] = model.get("kind") or "module"
        model["calls"] = calls
        model["seed"] = model.get("seed") or 0
        model["note"] = ("J v3 Task 5.5: structurally derived call expressions "
                         "(annotation > parameter-name > constant seeds; "
                         "non-terminating callables skipped; falsy profile for "
                         "loops without body progress)")
        record["input_model"] = model
        record["derivation"] = why or "derived"
        if notes:
            record["call_static"] = notes
        if calls:
            stats["calls_derived"] = 1
        else:
            stats["calls_empty"] = 1
    # ---- v3 台账口径：`excluded` 只表示「无可执行入口」，不表示「已判定」 ----
    # J v2 把「Task 5.3 模块级降级」写成 excluded 理由，而 coverage_checker 的
    # `excluded` 是**排除标记**（一旦非空就整体跳过 C1–C5）。v3 已对这些条目
    # 派生/保留了调用入口，故必须同时清空理由列表并改写 status，否则 637 条
    # 明明可执行的记录会被整批判成 excluded（实测首轮 1107 条 excluded）。
    if record["input_model"].get("calls"):
        record["excluded"] = []
        record["status"] = "callable"
    else:
        record["status"] = "excluded"
    return record, stats


def main(argv=None) -> int:
    """CLI 入口：读 J v2 清单 → 出 J v3 清单 + 备料报告。"""
    parser = argparse.ArgumentParser(description="J 空间 v3 备料器（pyc 重编译 + calls 派生）")
    parser.add_argument("--space", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--pyc-dir", required=True)
    parser.add_argument("--report", default="")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--version", action="version", version=TOOL_VERSION)
    args = parser.parse_args(argv)
    space = load(args.space)
    entries = space.get("entries") or []
    total_stats = collections.Counter()
    records = []
    per_entry = []
    for index, entry in enumerate(entries):
        if args.limit and index >= args.limit:
            break
        record, stats = prepare_entry(entry, args.pyc_dir)
        records.append(record)
        total_stats.update(stats)
        per_entry.append({"id": entry.get("id"), "pyc_provenance": record.get("pyc_provenance"),
                          "derivation": record.get("derivation"),
                          "calls": (record.get("input_model") or {}).get("calls")})
    out = dict(space)
    out["j_schema_version"] = "v3"
    out["base_space_sha256"] = digest(space)
    out["preparer"] = {"tool": "jspace_v3_prepare", "version": TOOL_VERSION}
    out["entry_status_policy"] = {
        "callable": "has executable call entrypoints; C1-C5 still unmeasured here",
        "excluded": "no executable call entrypoint; C1-C5 skipped by coverage_checker",
        "excluded_field": "only non-empty for entries without call entrypoints",
    }
    out["entries"] = records
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    report = {
        "tool": "jspace_v3_prepare", "version": TOOL_VERSION,
        "space": args.space, "out": args.out, "entries": len(records),
        "stats": dict(total_stats),
        "with_calls": sum(1 for r in records if (r.get("input_model") or {}).get("calls")),
        "without_calls": sum(1 for r in records if not (r.get("input_model") or {}).get("calls")),
        "derivation_reasons": dict(collections.Counter(
            str(r.get("derivation")) for r in records
            if not (r.get("input_model") or {}).get("calls"))),
        "static_skips": {
            "skipped_non_terminating": sorted({name for r in records
                                               for name in ((r.get("call_static") or {})
                                                            .get("skipped_non_terminating") or [])}),
            "falsy_variants": sorted({name for r in records
                                      for name in ((r.get("call_static") or {})
                                                   .get("falsy_variants") or [])}),
        },
        "entries_detail": per_entry,
    }
    if args.report:
        with open(args.report, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
    print("[jspace_v3_prepare] entries=%d pyc_regenerated=%d pyc_failed=%d with_calls=%d without_calls=%d"
          % (report["entries"], total_stats["pyc_regenerated"], total_stats["pyc_failed"],
             report["with_calls"], report["without_calls"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
