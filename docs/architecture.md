# 数据和可扩展接口

## 知识点

```json
{
  "id": "2.18.d",
  "ref": "2.18",
  "kind": "definition",
  "chapter": 2,
  "title": "闭集",
  "aliases": ["closed", "set"],
  "statement": "E 是闭集，当且仅当 E 的每个聚点都属于 E。",
  "intuition": "中文学习表述；核对原文。",
  "status": "reviewed",
  "source": {"pdf_page": 41, "pdf_end": 41, "printed_page": 29},
  "raw": "对应的原文条目"
}
```

同一编号可以细分多个概念，如 `2.18.a` 至 `2.18.j`。`ref` 保留教材编号。`source` 用于原文追溯，PDF 页码从 1 开始。图中边的方向固定为使用者→被使用者。

| 关系 | 解释 |
| --- | --- |
| `uses_definition` | 定理/概念表述或证明使用这个定义 |
| `depends_on` | 证明使用一个已有结果 |
| `references` | 原文明示引用，未判定数学依赖 |
| `specializes` | 目标知识的特殊情形 |
| `equivalent_to` | 在记录的条件下等价 |
| `implies` | 在记录的条件下蕴含 |

后面三种关系预留类型，当前种子没有自动填充。等价关系若需双向遍历，应记录两条方向边；依赖路径默认只遍历 `depends_on` 和 `uses_definition`。

状态：`indexed` 是机器原文索引，`reviewed` 是已对照教材的标注，`pending` 是待核对；LLM 候选保存在提案表位置而不是正式节点中。

## 代码入口

| 文件 | 职责与扩展点 |
| --- | --- |
| `config.py` | 路径、环境变量，路径相对项目根目录 |
| `ingest.py` | PyMuPDF 文本与页码、条目切分、明确引用 |
| `store.py` | SQLite 节点、图遍历、检索、向量 |
| `providers.py` | `ChatProvider`、`EmbeddingProvider` Protocol 和兼容 HTTP 实现；可新增其他协议实现 |
| `tools.py` | 网页、Agent、MCP 共享的知识工具及参数 schema |
| `agent.py` | 候选检索、多轮调用、证据收集、引用范围检查 |
| `mcp_client.py` | Agent 工具调用的 local/MCP 传输选择 |
| `mcp_server.py` | MCP 工具、资源、提示词；独立 stdio/HTTP 服务 |
| `extract.py` | 模型候选、目标验证、原文证据校验、核对事务 |
| `api.py` | REST、PDF 查看、本地网页 |
| `cli.py` | 初始化、启动、问答、分批抽取、向量与导出 |
| `web/` | 不依赖 CDN 的原生 HTML/CSS/JS 与 SVG 图谱 |

`Agent(store, provider=你的ChatProvider实例)` 和 `enrich(store,id,provider=实例)` 可注入模型。嵌入配置默认独立；若要更换嵌入协议，替换 `OpenAICompatibleEmbedding` 的创建位置，或者进一步改为依赖注入。

## 当前边界

- 图谱是局部展示，单次最多显示 40 个节点，原文引用默认隐藏；全图可 JSON 导出。
- 默认中文标注覆盖核心链条，全书索引条目不等于全书定义、命题或依赖穷尽。
- 源 PDF 是数字文本版，未实现扫描版 OCR；上下标、分式、数学符号的 PDF 提取可能失真。
- 中文学习表述使用 Unicode 数学符号；未集成 LaTeX 排版引擎。
- 初步检索加工具返回占用模型上下文，工具内容设有长度截断；复杂长证明应逐步问答。
- 本地无认证；如需共享部署，应另加身份认证、访问隔离、请求限流和持久化部署配置。
- LLM 抽取增强当前知识点。若某编号包含多个定义，需要进一步拆分节点并建立细粒度关系。
- 同一 SQLite 文件供网页和 MCP 使用；不要在服务运行中重建数据库。
