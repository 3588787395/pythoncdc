## ADDED Requirements

### Requirement: opencode 经 MCP 可查询知识库
LLM Wiki 自带 MCP server（`mcp-server/dist/src/index.js`，stdio，要求 node ≥ 20）SHALL 被注册进 opencode 配置（`~/.config/opencode/opencode.jsonc`），使 agent 至少可使用 `llm_wiki_status`、`llm_wiki_search`、`llm_wiki_read_file`、`llm_wiki_graph`、`llm_wiki_rescan_sources` 工具。

#### Scenario: agent 编码前先查知识库
- **WHEN** agent 接到涉及某反编译模块（如 region 归约）的修改任务，且 LLM Wiki 应用运行中
- **THEN** agent 可先调用 `llm_wiki_search` 命中相关概念/模块页，再据此决定修改方式

#### Scenario: 应用未运行时优雅降级
- **WHEN** LLM Wiki 应用未运行导致 MCP 工具连接失败
- **THEN** agent 继续以无知识库模式工作，且不将该失败误报为任务成功依据

### Requirement: Obsidian 可视化浏览
LLM Wiki 应用数据目录 SHALL 被注册为 Obsidian vault，其中知识库页面可被 Obsidian 正常渲染，反向链接面板可用。

#### Scenario: 打开 vault 浏览页面
- **WHEN** 在 Obsidian 中打开该 vault
- **THEN** 种子页面可见且正文渲染正常，打开任一页可在反链面板看到引用它的页面

### Requirement: 种子化三批次
知识库 SHALL 按序完成三个种子批次：(1) 概念页 `ast-generation-lineages`——呈现三代 AST 生成谱系（region 系 / v2 系 / 自包含 control_flow）与三胞胎 ast_builder 的 import 关系；(2) 白名单全部源文件的模块骨架页；(3) 补丁热点页——将补丁标记聚类为若干热点并链接对应模块页。

#### Scenario: 谱系概念页可回答"哪套生成器活着"
- **WHEN** 查询"三代生成器中哪套从入口可达"
- **THEN** `ast-generation-lineages` 页给出 import 路径证据（含 `pycdc.py:84` → RegionASTGenerator 等锚点）

#### Scenario: 模块骨架页全覆盖
- **WHEN** 对白名单文件列表与 `modules/` 页面列表做差集
- **THEN** 差集为空（每个白名单文件恰有一页骨架页）

#### Scenario: 热点页驱动重构清单
- **WHEN** 从热点页出发沿 wikilink 与其 Dataview 查询
- **THEN** 可得到按补丁标记数排序的模块/聚类清单，作为重构候选输入
