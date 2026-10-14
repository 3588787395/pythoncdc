"""补丁标记语义聚类：把 PATCH_RE 命中的行按缺陷/关注类型分类。

口径与 gen_modules.py 完全一致（同一 PATCH_RE，同一白名单）。
输出：docs/refactor/patch-semantic-clusters.json + stdout 汇总表。

主类判定：取行内最早出现的关键词所属类（位置并列时按 CLASSES 声明序）。
前缀方法（def _fix_/_patch_/...）单独计数并列出方法名（G3 反模式自检素材）。
"""

import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "refactor" / "patch-semantic-clusters.json"
WL_DIRS = ["core", "parsers", "bytecode", "utils"]

PATCH_RE = re.compile(
    r"#.*(?:修复|补丁|临时|workaround|hack|兼容|hardcode|硬编码)|"
    r"def\s+_(?:fix|merge|patch|fallback|hack|workaround|temp)_",
    re.IGNORECASE,
)

DEF_PREFIX_RE = re.compile(
    r"def\s+_(fix|merge|patch|fallback|hack|workaround|temp)_\w*", re.IGNORECASE
)

# (类名, 关键词正则)。声明序即同位置时的优先序。
# 注：循环引用/循环依赖 ≠ 循环控制流，用负向先行排除出 loop-boundary。
CLASSES = [
    ("dedup-orphan", re.compile(r"去重|重复生成|重复处理|孤儿|漏生成|丢失|缺失|多余|冗余|唯一归属", re.IGNORECASE)),
    ("ordering", re.compile(r"排序|顺序|偏移量|先后|插入位置", re.IGNORECASE)),
    ("loop-boundary", re.compile(r"循环(?!引用|依赖)|回边|loop|while|for_|迭代(?!器)?$|continue|break", re.IGNORECASE)),
    ("if-elif-else", re.compile(r"elif|分支|条件(?:判断|块)?|if_|嵌套if|if块", re.IGNORECASE)),
    ("boolop-chain", re.compile(r"boolop|短路|复合条件|and链|or链|and/or", re.IGNORECASE)),
    ("try-except", re.compile(r"try|except|finally|异常|reraise|raise", re.IGNORECASE)),
    ("with-context", re.compile(r"with|上下文|context", re.IGNORECASE)),
    ("match-case", re.compile(r"match|匹配|case", re.IGNORECASE)),
    ("comprehension", re.compile(r"推导|comprehension|列表式|生成器表达式", re.IGNORECASE)),
    ("ternary", re.compile(r"三元|ternary|ifexp", re.IGNORECASE)),
    ("version-compat", re.compile(r"版本|兼容|3\.(9|10|11|12|13)|version|PEP\d*|cpython", re.IGNORECASE)),
    ("hardcode-magic", re.compile(r"硬编码|hardcode|魔数|magic|写死", re.IGNORECASE)),
    ("perf-cache", re.compile(r"性能|缓存|cache|加速|优化|慢", re.IGNORECASE)),
    ("fallback", re.compile(r"回退|fallback|降级|兜底", re.IGNORECASE)),
]
OTHER = "other"


def collect_files():
    files = []
    for d in WL_DIRS:
        files += sorted((ROOT / d).rglob("*.py"))
    files += [ROOT / "pycdc.py", ROOT / "pycdas.py"]
    return files


def primary_class(line: str):
    best, best_pos = OTHER, None
    for name, rx in CLASSES:
        m = rx.search(line)
        if m and (best_pos is None or m.start() < best_pos):
            best, best_pos = name, m.start()
    return best


def main():
    total = 0
    primary = Counter()
    multi = Counter()
    per_file = defaultdict(Counter)
    samples = defaultdict(list)
    prefix_methods = Counter()
    for f in collect_files():
        rel = f.relative_to(ROOT).as_posix()
        text = f.read_bytes().decode("utf-8", errors="replace")
        for i, line in enumerate(text.splitlines(), 1):
            if not PATCH_RE.search(line):
                continue
            total += 1
            dm = DEF_PREFIX_RE.search(line)
            if dm:
                prefix_methods[f"_{dm.group(1).lower()}_"] += 1
                cls = "prefix-method"
            else:
                cls = primary_class(line)
            primary[cls] += 1
            per_file[rel][cls] += 1
            hits = [name for name, rx in CLASSES if rx.search(line)]
            for h in hits or [OTHER]:
                multi[h] += 1
            if len(samples[cls]) < 8 and "# " in line:
                samples[cls].append({"file": rel, "line": i, "text": line.strip()[:120]})

    result = {
        "generated": date.today().isoformat(),
        "total_markers": total,
        "primary": dict(primary.most_common()),
        "multi_label": dict(multi.most_common()),
        "prefix_methods": dict(prefix_methods.most_common()),
        "per_file_top": {
            rel: dict(c.most_common(5))
            for rel, c in sorted(per_file.items(), key=lambda kv: -sum(kv[1].values()))[:15]
        },
        "samples": {k: v for k, v in samples.items() if v},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    print(f"total markers: {total}")
    print(f"{'class':<18}{'primary':>8}{'multilabel':>12}")
    for name, _ in CLASSES + [(OTHER, None), ("prefix-method", None)]:
        p = primary.get(name, 0)
        m = multi.get(name, 0) if name != "prefix-method" else prefix_methods and sum(prefix_methods.values())
        print(f"{name:<18}{p:>8}{m:>12}")
    print(f"\nJSON -> {OUT}")


if __name__ == "__main__":
    main()
