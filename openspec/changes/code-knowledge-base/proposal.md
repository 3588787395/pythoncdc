## Why

反编译器核心代码约 22 万行（core/parsers/bytecode 等），已积累三代并存的 AST 生成谱系（region 系 / v2 系 / 自包含 control_flow）、三胞胎 ast_builder、双份 code_generator、8,954 个补丁标记——这些复杂度事实只存在于代码里，现有五层文档描述的是"意图"而非"现状"，且 11,586 个 .trae 迭代现场无人能回读。需要一个**从代码本身生成**的知识库，让人类（Obsidian 图谱/反链）和 agent（opencode 经 MCP 查询）在做任何重构决策前，先看到代码真实结构，从而降低复杂度、提升算法通用性。

## What Changes

- 首次运行 LLM Wiki 0.6.10 便携版，创建绑定 `F:\Downloads\pythoncdc-main` 的 project，**sources 仅圈定反编译器代码**（core/ parsers/ bytecode/ utils/ pycdc.py pycdas.py），排除 tests/ .trae/ scripts/ docs/ site-packages/
- 将便携版自带的 MCP server（`mcp-server/dist/src/index.js`，stdio）注册进 opencode 配置，使 agent 编码前可 `llm_wiki_search` 查询知识库
- 用 Obsidian 打开 LLM Wiki 应用数据目录作为 vault（graph / 反链 / Dataview）
- 种子化知识库（按信息密度排序的三个批次）：
  1. 概念页 `ast-generation-lineages`（三代谱系 import 图——已探明大半）
  2. 全量模块骨架页（~55 个文件的 metrics/frontmatter，机器提取）
  3. 补丁热点页（8,954 个 patch marker 聚类 → 重构目标清单）
- 建立同步约定：代码变更 → `llm_wiki_rescan_sources` → stale 页面标记 → 定向重写
- 制定页面 schema（AGENTS 约定：页面类型、frontmatter 字段、命名规则），人与 LLM 共同演化

## Capabilities

### New Capabilities

- `code-kb-sources`: 知识库的源范围界定与增量重扫描——跟踪哪些代码目录、如何排除非反编译器内容、代码变更后如何触发重扫描与 stale 检测
- `code-kb-pages`: 页面分类学与 frontmatter schema——modules/classes/concepts/hotspots 四类页面的结构、必填字段（file、content_hash、metrics）、命名与 `[[wikilink]]` 规则
- `code-kb-query`: 双端访问——opencode 经 MCP 工具查询（search/read/graph/rescan）与人类经 Obsidian 浏览（graph/反链/Dataview 仪表盘），及首次种子化批次的内容要求

### Modified Capabilities

（无——`openspec/specs/` 当前为空，无既有能力的需求变更）

## Impact

- **配置**：`~/.config/opencode/opencode.jsonc` 新增 MCP server 条目（指向便携目录，要求 node ≥ 20，本机 v24 ✓）
- **环境**：LLM Wiki.exe 首次运行（应用数据目录待首启后确认）；Obsidian 新增一个 vault 指向该目录
- **仓库代码**：本变更**不修改**任何反编译器源码；仓库内仅新增 OpenSpec 变更目录（本目录）
- **依赖**：LLM Wiki 本地 API `127.0.0.1:19828` 需在应用运行时可用；MCP 查询仅在应用运行时可用
- **风险**：应用数据目录位置与页面 md 格式的 Obsidian 兼容性为待验事实（首启后确认，见 design.md 未知项）
