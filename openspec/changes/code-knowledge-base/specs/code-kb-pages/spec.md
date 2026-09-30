## ADDED Requirements

### Requirement: 四类页面分类学
知识库 SHALL 维护四类页面：`modules/`（每个白名单源文件一页的骨架页）、`classes/`（核心类页，含继承与 override 信息）、`concepts/`（LLM 综述的算法/结构概念页）、`hotspots/`（补丁标记聚类页）。每页 MUST 归属且仅归属一类。

#### Scenario: 新模块文件入库
- **WHEN** 白名单内出现新的 `.py` 文件并完成扫描
- **THEN** `modules/` 下生成对应该文件的骨架页

#### Scenario: 概念页独立于模块页存在
- **WHEN** 创建"三代 AST 生成谱系"综述页
- **THEN** 该页位于 `concepts/` 并通过 `[[wikilink]]` 引用相关 `modules/` 页，而非塞进任一模块页

### Requirement: frontmatter 必填字段
所有骨架页（modules/classes）frontmatter SHALL 含：`file`（仓库相对路径）、`content_hash`、`kind`（module|class）、代码规模指标（`lines`；可得时含 `patch_markers`、`method_count`）。概念页/热点页 frontmatter SHALL 含 `kind`（concept|hotspot）与 `sources`（其依据的源文件或页面列表）。

#### Scenario: Dataview 可按指标查询
- **WHEN** 在 Obsidian 中执行 Dataview 查询 `WHERE kind = "module" AND patch_markers > 100`
- **THEN** 返回所有补丁标记超阈值的模块页，构成重构目标清单

#### Scenario: 概念页标注依据
- **WHEN** 阅读任一 `concepts/` 页
- **THEN** frontmatter `sources` 列出其结论所依据的源文件，正文含 `file:line` 级引用锚点

### Requirement: 链接与命名规则
页面文件名与 `[[wikilink]]` 目标 SHALL 使用 kebab-case 英文（正文可用中文），以规避 Windows/编码路径问题；任一页面内的 wikilink MUST 指向存在的页面或在 lint 中被报告为断链。

#### Scenario: 断链可检测
- **WHEN** 运行知识库 lint（应用内或 MCP 侧健康检查）
- **THEN** 指向不存在页面的 `[[wikilink]]` 被列为待修复项

### Requirement: 总索引页
知识库 SHALL 维护一个总索引页（如 `index.md`），按四类页面分节列出链接，并作为 Obsidian 打开 vault 的入口。

#### Scenario: 从索引到达任一类页面
- **WHEN** 打开总索引页
- **THEN** modules/classes/concepts/hotspots 四类均有入口链接，经一跳可达任一已有页面
