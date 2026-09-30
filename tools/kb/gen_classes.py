import ast
import hashlib
from datetime import date
from pathlib import Path

ROOT = Path(r"F:\Downloads\pythoncdc-main")
CLASSES = ROOT / "wiki" / "classes"
WL_DIRS = ["core", "parsers", "bytecode", "utils"]
TODAY = date.today().isoformat()
MIN_METHODS = 8


def collect_files():
    files = []
    for d in WL_DIRS:
        files += sorted((ROOT / d).rglob("*.py"))
    files += [ROOT / "pycdc.py", ROOT / "pycdas.py"]
    return files


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


def module_slug(rel: Path) -> str:
    return str(rel.with_suffix("")).replace("\\", "/").replace("/", "-").replace("_", "-").lower()


def first_doc(node) -> str:
    d = ast.get_docstring(node)
    if not d:
        return ""
    return d.strip().splitlines()[0][:80]


def main():
    CLASSES.mkdir(exist_ok=True)
    files = collect_files()
    # index: class name -> (methods set, file) for override detection
    class_index = {}
    parsed = []
    for f in files:
        rel = f.relative_to(ROOT)
        text = f.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(text.lstrip(chr(0xFEFF)))
        except SyntaxError:
            continue
        parsed.append((rel, f, text, tree))
        for n in ast.walk(tree):
            if isinstance(n, ast.ClassDef):
                meths = {m.name for m in n.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))}
                class_index[n.name] = (meths, rel)

    pages = []
    for rel, f, text, tree in parsed:
        md5 = hashlib.md5(f.read_bytes()).hexdigest()
        mslug = module_slug(rel)
        lines_all = text.splitlines()
        for n in ast.walk(tree):
            if not isinstance(n, ast.ClassDef):
                continue
            methods = [m for m in n.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
            if len(methods) < MIN_METHODS:
                continue
            end = max((m.end_lineno or m.lineno) for m in methods) if methods else n.lineno
            bases = [ast.unparse(b) if hasattr(ast, "unparse") else "?" for b in n.bases]
            overrides = []
            for b in bases:
                bname = b.split(".")[-1].split("(")[0]
                if bname in class_index and bname != n.name:
                    bmeths, bfile = class_index[bname]
                    common = sorted({m.name for m in methods} & bmeths)
                    if common:
                        overrides.append(f"{bname}: {', '.join(common[:12])}")
            slug = f"{mslug}--{kebab_class(n.name)}"
            fm = [
                "---",
                "type: entity",
                f"title: {n.name}",
                "tags:",
                "  - code-kb",
                f'related:',
                f'  - "[[{mslug}]]"',
                f"created: {TODAY}",
                f"updated: {TODAY}",
                "kind: class",
                f"file: {rel.as_posix()}",
                f"content_hash: {md5}",
                f"class: {n.name}",
                f"defined_at: {rel.as_posix()}:{n.lineno}",
                f"class_lines: {end - n.lineno + 1}",
                f"method_count: {len(methods)}",
                f"bases: [{', '.join(bases)}]" if bases else "bases: []",
                "sources:",
                f"  - {rel.as_posix()}",
                "---",
                "",
            ]
            doc = first_doc(n)
            body = [
                f"# {n.name}",
                "",
                f"定义于 `{rel.as_posix()}:{n.lineno}`（类体 {end - n.lineno + 1} 行，{len(methods)} 个方法），所属模块 [[{mslug}]]。",
                "",
            ]
            if doc:
                body += [f"> {doc}", ""]
            body += ["## 继承与 override", ""]
            if not bases:
                body += ["- 无基类（模块内独立定义）", ""]
            else:
                for b in bases:
                    bname = b.split(".")[-1].split("(")[0]
                    known = bname in class_index
                    body.append(f"- `{b}`" + ("" if known else "（仓库外/未建页）"))
                body.append("")
                if overrides:
                    body += ["override（与仓库内基类同名方法）：", ""]
                    body += [f"- {o}" for o in overrides]
                    body.append("")
                else:
                    body += ["- 仓库内基类无同名方法 override", ""]
            body += [
                "## 方法清单",
                "",
            ]
            for m in sorted(methods, key=lambda x: x.lineno):
                body.append(f"- `{m.name}()` :{m.lineno}")
            body += ["", "## 相关页面", "", f"- [[{mslug}|{rel.as_posix()}]]", "- [[index|Wiki Index]]", ""]
            (CLASSES / f"{slug}.md").write_text("\n".join(fm + body), encoding="utf-8", newline="\n")
            pages.append((rel.as_posix(), n.name, slug, len(methods)))
    return pages


if __name__ == "__main__":
    pages = main()
    print(f"generated {len(pages)} class pages")
