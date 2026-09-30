# Wiki Schema

## Page Types

| Type | Directory | Purpose |
|------|-----------|---------|
| entity | wiki/entities/ | Named things (people, tools, organizations, datasets) |
| concept | wiki/concepts/ | Ideas, techniques, phenomena, frameworks |
| source | wiki/sources/ | Papers, articles, talks, books, blog posts |
| query | wiki/queries/ | Open questions under active investigation |
| comparison | wiki/comparisons/ | Side-by-side analysis of related entities |
| synthesis | wiki/synthesis/ | Cross-cutting summaries and conclusions |
| overview | wiki/ | High-level project summary (one per project) |

### Code KB page types (pythoncdc 白名单代码知识库)

| kind | Directory | Purpose |
|------|-----------|---------|
| module | wiki/modules/ | 每个白名单源文件一页的骨架页（file/lines/patch_markers 等） |
| class | wiki/classes/ | 核心类页（继承、override、方法清单） |
| concept | wiki/concepts/ | LLM 综述的算法/结构概念页（如三代 AST 谱系） |
| hotspot | wiki/hotspots/ | 补丁标记聚类页（聚类位置 → 对应 modules/ 页） |
| pattern | wiki/patterns/ | 缺陷模式页（症状 → 区域类型 → 边界判据 → 原则 → 修复锚点 + 检索词；从 rules.md 修复案例与补丁语义聚类提炼） |

- 每页 MUST 归属且仅归属一类；文件名 `kebab-case.md` 英文，正文中文。
- 概念/热点页通过 `[[wikilink]]` 引用相关 `modules/` 页，不把综述塞进模块页。
- 为兼容应用 Knowledge 树的 `type` 字段映射：module/class → `type: entity`，concept/pattern → `type: concept`，hotspot → `type: synthesis`。

## Naming Conventions

- Files: `kebab-case.md`
- Entities: match official name where possible (e.g., `openai.md`, `gpt-4.md`)
- Concepts: descriptive noun phrases (e.g., `chain-of-thought.md`)
- Sources: `author-year-slug.md` (e.g., `wei-2022-cot.md`)
- Queries: question as slug (e.g., `does-scale-improve-reasoning.md`)

## Frontmatter

All pages must include YAML frontmatter:

```yaml
---
type: entity | concept | source | query | comparison | synthesis | overview
title: Human-readable title
tags: []
related: []
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

Source pages also include:
```yaml
authors: []
year: YYYY
url: ""
venue: ""
```

### Code KB required fields

骨架页（`wiki/modules/`、`wiki/classes/`）frontmatter SHALL 含：

```yaml
kind: module | class
file: 仓库相对路径          # e.g. core/region_analyzer.py
content_hash: <md5 小写十六进制>  # 源文件原始字节的 MD5，用于 stale 判定
lines: <int>               # 源文件行数
patch_markers: <int>       # 该文件补丁标记数（可得时）
method_count: <int>        # 方法/函数数（可得时）
sources: []                # 生成本页所依据的源文件或页面
```

概念页/热点页/模式页（`wiki/concepts/`、`wiki/hotspots/`、`wiki/patterns/`）frontmatter SHALL 含：

```yaml
kind: concept | hotspot | pattern
sources: []                # 依据的源文件或页面列表
```

- 模式页正文 SHALL 含统一小节：症状 / 根因（违反的原则）/ 边界判定规则 / 修复锚点 / 已知案例 / 检索词——检索词小节是 Q4"修复前先查 wiki"能否命中的关键，必须列出该缺陷的常见症状表述（中英）。

- Dataview 查询约定：`TABLE lines, patch_markers FROM #kind WHERE kind = "module" AND patch_markers > 100`
- stale 判定：`content_hash` 与当前源文件 MD5 不一致即为 stale。
- **写入本仓库的 JSON/Markdown 一律无 BOM**（UTF-8 no BOM；LLM Wiki 解析器不容忍 BOM）。

## Index Format

`wiki/index.md` lists all pages grouped by type. Each entry:
```
- [[page-slug]] — one-line description
```

## Log Format

`wiki/log.md` records activity in reverse chronological order:
```
## YYYY-MM-DD

- Action taken / finding noted
```

## Cross-referencing Rules

- Use `[[page-slug]]` syntax to link between wiki pages
- Every entity and concept should appear in `wiki/index.md`
- Queries link to the sources and concepts they draw on
- Synthesis pages cite all contributing sources via `related:`

## Contradiction Handling

When sources contradict each other:
1. Note the contradiction in the relevant concept or entity page
2. Create or update a query page to track the open question
3. Link both sources from the query page
4. Resolve in a synthesis page once sufficient evidence exists
