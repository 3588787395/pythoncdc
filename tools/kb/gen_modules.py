import ast
import hashlib
import re
from datetime import date
from pathlib import Path

ROOT = Path(r"F:\Downloads\pythoncdc-main")
MODULES = ROOT / "wiki" / "modules"
CLASSES = ROOT / "wiki" / "classes"
WL_DIRS = ["core", "parsers", "bytecode", "utils"]
TODAY = date.today().isoformat()

PATCH_RE = re.compile(
    r"#.*(?:修复|补丁|临时|workaround|hack|兼容|hardcode|硬编码)|"
    r"def\s+_(?:fix|merge|patch|fallback|hack|workaround|temp)_",
    re.IGNORECASE,
)


def collect_files():
    files = []
    for d in WL_DIRS:
        files += sorted((ROOT / d).rglob("*.py"))
    files += [ROOT / "pycdc.py", ROOT / "pycdas.py"]
    return files


def kebab(rel: Path) -> str:
    return str(rel.with_suffix("")).replace("\\", "/").replace("/", "-").replace("_", "-").lower()


def kebab_class(name: str) -> str:
    out = []
    for i, ch in enumerate(name):
        if ch.isupper():
            prev = name[i - 1] if i > 0 else ""
            nxt = name[i + 1] if i + 1 < len(name) else ""
            if out and (prev.islower() or prev.isdigit() or (prev.isupper() and nxt.islower())):
                out.append("-")
            out.append(ch.lower())
        elif ch.isalnum():
            out.append(ch.lower())
        else:
            out.append("-")
    return "".join(out).strip("-")


def parse(text: str):
    return ast.parse(text.lstrip("﻿"))


def metrics(text: str, tree):
    lines = len(text.splitlines())
    methods = None
    if tree is not None:
        methods = sum(
            isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in ast.walk(tree)
        )
    patch = len(PATCH_RE.findall(text))
    return lines, methods, patch


def summary_and_symbols(rel: Path, slug: str, tree):
    doc = ast.get_docstring(tree) if tree is not None else None
    first = doc.strip().splitlines()[0][:120] if doc else ""
    classes, funcs = [], []
    if tree is not None:
        for n in tree.body:
            if isinstance(n, ast.ClassDef):
                classes.append(n)
            elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                funcs.append(n)
    if not first:
        first = f"模块含 {len(classes)} 个类、{len(funcs)} 个顶层函数。"
    summary = [first, ""]
    if tree is None:
        summary = ["（语法解析失败——文件含 BOM/语法错误，摘要待人工补充）", ""]
    symbols = ["### 类", ""]
    if classes:
        for c in classes:
            cslug = f"{slug}--{kebab_class(c.name)}"
            link = f"[[{cslug}|{c.name}]]" if (CLASSES / f"{cslug}.md").exists() else f"`{c.name}`"
            symbols.append(f"- {link} :{c.lineno}")
    else:
        symbols.append("- （无顶层类）")
    symbols += ["", "### 顶层函数", ""]
    if funcs:
        top = sorted(funcs, key=lambda m: -((m.end_lineno or m.lineno) - m.lineno))[:20]
        for fn in sorted(top, key=lambda m: m.lineno):
            symbols.append(f"- `{fn.name}()` :{fn.lineno}")
        if len(funcs) > 20:
            symbols.append(f"- …共 {len(funcs)} 个顶层函数，仅列体长前 20")
    else:
        symbols.append("- （无顶层函数）")
    return summary, symbols, len(classes), len(funcs)


def build(rel: Path, f: Path):
    data = f.read_bytes()
    md5 = hashlib.md5(data).hexdigest()
    text = data.decode("utf-8", errors="replace")
    try:
        tree = parse(text)
    except SyntaxError:
        tree = None
    lines, methods, patch = metrics(text, tree)
    slug = kebab(rel)
    summary, symbols, n_classes, n_funcs = summary_and_symbols(rel, slug, tree)
    fm = [
        "---",
        "type: entity",
        f"title: {f.name}",
        "tags:",
        "  - code-kb",
        "related: []",
        f"created: {TODAY}",
        f"updated: {TODAY}",
        "kind: module",
        f"file: {rel.as_posix()}",
        f"content_hash: {md5}",
        f"lines: {lines}",
        f"patch_markers: {patch}",
    ]
    if methods is not None:
        fm.append(f"method_count: {methods}")
    fm += ["sources:", f"  - {rel.as_posix()}", "---", ""]
    metrics_rows = [f"| lines | {lines} |", f"| patch_markers | {patch} |"]
    if methods is not None:
        metrics_rows.append(f"| method_count | {methods} |")
    metrics_rows.append(f"| 顶层类/函数 | {n_classes}/{n_funcs} |")
    body = [
        f"# {rel.as_posix()}",
        "",
        f"源文件：`{rel.as_posix()}`（{lines} 行，md5 `{md5}`）",
        "",
        "## 指标",
        "",
        "| 指标 | 值 |",
        "|---|---|",
        *metrics_rows,
        "",
        "## 摘要",
        "",
        *summary,
        "## 关键符号",
        "",
        *symbols,
        "",
        "## 相关页面",
        "",
        "- [[index|Wiki Index]]",
        "",
    ]
    return slug, "\n".join(fm + body)


def main():
    MODULES.mkdir(exist_ok=True)
    pages = []
    for f in collect_files():
        rel = f.relative_to(ROOT)
        slug, content = build(rel, f)
        (MODULES / f"{slug}.md").write_text(content, encoding="utf-8", newline="\n")
        pages.append((rel.as_posix(), slug))
    return pages


if __name__ == "__main__":
    pages = main()
    print(f"generated {len(pages)} module pages")
