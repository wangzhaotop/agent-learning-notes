# agent-learning-notes

使用 Python 学习并构建 AI Agent 的完整实践项目，从基础到生产化部署。路线图见 [ROADMAP.md](ROADMAP.md)。

## 项目简介

本项目是一个**从零到一的 Agent 开发学习路径**，覆盖 7 个阶段：

1. **裸调 LLM API**：理解 messages、system prompt、流式、JSON mode
2. **手写 Agent**：从零实现 tool calling、ReAct 循环、多轮记忆
3. **RAG 与上下文工程**：向量检索、切块策略、窗口管理、摘要压缩
4. **工程化**：装饰器注册、Pydantic 校验、单元测试、模块化设计
5. **MCP 协议**：Model Context Protocol 实战，理解工具连接标准
6. **多 Agent 编排**：链式、路由、并行、orchestrator-workers 四大模式
7. **生产化部署**：Instructor 结构化输出、mem0 长期记忆、FastAPI 服务化、Milvus 向量库、可观测与评测

## 学习路线

| 阶段 | 目录 | 主题 | 核心技能 | 状态 |
|------|------|------|----------|------|
| 0 | `00_python基础/` | Python 基础补强 | 函数/容器/OOP/装饰器/迭代器 | ✅ 已完成 |
| 1 | `01_LLM/` | 裸调 LLM API | messages 结构、流式、JSON mode | ✅ 已毕业 |
| 2 | `02_agent/` | 手写 Agent | function calling、ReAct 循环 | ✅ 已毕业 |
| 3 | `03_rag/` | RAG 与上下文工程 | 向量检索、切块、窗口管理 | ✅ 已毕业 |
| 4 | `04_engineering/` | Agent 工程化 | 装饰器、Pydantic、pytest、模块化 | ✅ 已毕业 |
| 5 | `05_mcp/` | MCP 协议 | MCP server/client、异步编程 | ✅ 已毕业 |
| 6 | `06_multi_agent/` | 多 Agent 编排 | 链式/路由/并行/orchestrator | 🔄 进行中 |
| 7 | `07_production/` | 生产化部署 | FastAPI、Milvus、mem0、可观测 | 📘 手册已就绪 |

**学习特色**：
- ✅ 每个阶段都有**完整学习手册**（目标 → 带注释代码 → 自测题 → 闭卷毕业考）
- ✅ **先手写后框架**：阶段 1-3 手写所有核心逻辑，理解原理后再用框架（阶段 4-7）
- ✅ **真实项目驱动**：每个阶段的毕业考都是完整的可运行项目
- ✅ **企业技能对齐**：阶段 7 的技术栈对标企业真实需求（FastAPI 服务化、Milvus 向量库、mem0 记忆管理、LLM-as-judge 评测）

## 快速开始

### 环境准备

```bash
# 1. 创建 conda 环境
conda create -n agent python=3.11
conda activate agent

# 2. 安装依赖
pip install openai python-dotenv pydantic pytest

# 阶段 3 额外依赖
pip install chromadb sentence-transformers

# 阶段 5 额外依赖
pip install mcp

# 阶段 7 额外依赖
pip install instructor mem0ai fastapi uvicorn sse-starlette pymilvus langsmith
```

### 配置 API Key

在项目根目录创建 `.env` 文件：

```bash
# LLM API 配置（示例：DeepSeek）
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_BASE_URL=https://api.deepseek.com
MODEL_NAME=deepseek-chat

# 阶段 7 可选配置
LANGSMITH_API_KEY=ls__...  # LangSmith 可观测（可选）
MEM0_API_KEY=...           # mem0 云端版（可选，本地模式无需）
```

### 开始学习

```bash
# 进入任意阶段目录
cd 01_LLM

# 阅读学习手册
cat 学习手册.md

# 运行示例代码
python 01_simple_chat.py

# 完成毕业考
python 04_graduation.py
```

## 项目结构

```
agent-learning-notes/
├── README.md                    # 本文件
├── ROADMAP.md                   # 完整学习路线图（7 个阶段的详细规划）
├── .env                         # API 配置（需自行创建，见上方示例）
├── .gitignore                   # Git 忽略规则
│
├── 00_python基础/               # 阶段 0：Python 专题补强（函数/装饰器/迭代器）
├── 01_LLM/                      # 阶段 1：裸调 LLM API
│   ├── 学习手册.md
│   ├── 01_simple_chat.py        # 简单对话
│   ├── 02_streaming.py          # 流式输出
│   ├── 03_json_mode.py          # JSON 结构化输出
│   └── 04_graduation.py         # 毕业考：多轮对话 + 历史管理
│
├── 02_agent/                    # 阶段 2：手写 Agent
│   ├── 学习手册.md
│   ├── 01_function_calling.py   # function calling 基础
│   ├── 02_simple_agent.py       # 手写 Agent 循环
│   ├── 03_react_agent.py        # ReAct 模式
│   └── 04_graduation.py         # 毕业考：多工具 Agent
│
├── 03_rag/                      # 阶段 3：RAG 与上下文工程
│   ├── 学习手册.md
│   ├── knowledge/               # 知识库文档（示例）
│   ├── 01_simple_rag.py         # 简单 RAG
│   ├── 02_chunking.py           # 切块策略
│   ├── 03_context_window.py     # 窗口管理
│   └── 04_rag_agent.py          # 毕业考：完整 RAG Agent
│
├── 04_engineering/              # 阶段 4：工程化
│   ├── 学习手册.md
│   ├── tools.py                 # 工具注册器（装饰器）
│   ├── agent.py                 # Agent 核心逻辑
│   ├── tests/                   # 单元测试
│   └── main.py                  # 入口
│
├── 05_mcp/                      # 阶段 5：MCP 协议
│   ├── 学习手册.md
│   ├── file_server.py           # MCP file server
│   ├── rag_server.py            # MCP RAG server
│   ├── client.py                # MCP client
│   └── agent_main.py            # MCP Agent
│
├── 06_multi_agent/              # 阶段 6：多 Agent 编排
│   ├── 学习手册.md
│   ├── 01_chain.py              # 链式（顺序执行）
│   ├── 02_router.py             # 路由（条件分发）
│   ├── 03_parallel.py           # 并行（同时执行）
│   └── 04_orchestrator.py       # orchestrator-workers
│
└── 07_production/               # 阶段 7：生产化部署
    ├── 学习手册.md
    ├── 01_instructor.py         # Instructor 结构化输出
    ├── 02_mem0_memory.py        # mem0 长期记忆
    ├── 03_fastapi_agent.py      # FastAPI 服务化 + SSE
    ├── 04_milvus_rag.py         # Milvus 向量数据库
    ├── 05_observability.py      # 可观测（LangSmith / Langfuse）
    ├── 06_evaluation.py         # 评测（LLM-as-judge）
    ├── 07_swarm_intro.py        # OpenAI Swarm 快速上手
    └── 08_knowledge_service.py  # 毕业考：企业知识库问答服务
```

## 技能树

完成本项目全部 7 个阶段后，你将掌握：

### 核心能力
- ✅ **Agent 原理**：手写 ReAct 循环、tool calling、多轮记忆管理
- ✅ **RAG 完整流程**：文档加载、切块、向量化、检索、重排序
- ✅ **上下文工程**：窗口管理、摘要压缩、长对话处理
- ✅ **多 Agent 编排**：4 种模式（链式、路由、并行、orchestrator-workers）

### 工程能力
- ✅ **模块化设计**：装饰器注册、依赖注入、错误处理
- ✅ **单元测试**：pytest 测试 Agent 的工具调用、推理链路
- ✅ **MCP 协议**：自定义 MCP server，理解工具连接标准
- ✅ **结构化输出**：Instructor + Pydantic 自动重试

### 生产能力
- ✅ **服务化**：FastAPI + SSE 流式，HTTP 接口部署
- ✅ **向量数据库**：Milvus 生产级向量库（持久化、分布式）
- ✅ **长期记忆**：mem0 跨会话记忆管理
- ✅ **可观测**：LangSmith / Langfuse 链路追踪、token 成本分析
- ✅ **自动评测**：LLM-as-judge 批量测试 Agent 质量

## 常见问题

### 1. 为什么选 Python 而不是 Java/Go？

Python 是 AI Agent 开发的**首选语言**：
- 主流框架（LangChain、LangGraph、AutoGen）都是 Python 优先
- 生态完善（OpenAI SDK、Anthropic SDK、向量库、embedding 模型）
- 社区最活跃，99% 的教程和开源项目都是 Python

### 2. 需要多久能学完？

- **快速通关**：每天 2 小时，2-3 周完成阶段 1-3（核心原理）
- **完整学习**：每天 1.5 小时，2-3 个月完成全部 7 阶段（可求职）
- **建议节奏**：周一到周五敲代码，周末做毕业考 + 自测题复盘

### 3. 没有 AI/ML 背景能学吗？

**能！** 本项目零门槛：
- 阶段 0 补强 Python 基础（函数、装饰器、迭代器）
- 阶段 1 从"调用 API"开始，不需要懂 Transformer / 反向传播
- 重点是**工程能力**（怎么把 Agent 做成可交付的服务），不是调参/训练

### 4. 和 LangChain 官方教程有什么区别？

| 维度 | LangChain 官方教程 | 本项目 |
|------|-------------------|--------|
| 起点 | 直接用框架 | 先手写原理，再用框架 |
| 深度 | 覆盖面广但浅 | 每个概念都有完整代码 + 毕业考 |
| 实战 | 示例代码片段 | 7 个完整可运行项目 |
| 生产化 | 较少涉及 | 阶段 7 专门讲部署/可观测/评测 |

**建议路径**：先学本项目（理解原理），再看 LangChain 文档（扩展知识面）

### 5. 学完能找工作吗？

**能，但需要补充**：
- ✅ **简历项目**：把阶段 7 的毕业考（企业知识库问答服务）改成你的真实需求（如你公司的内部文档），写成完整项目
- ✅ **开源贡献**：给 LangChain / mem0 提 PR，或发布你的 Agent 项目到 GitHub
- ✅ **技术博客**：写 3-5 篇深度文章（如"手写 Agent 的 7 个坑"、"RAG 切块策略对比实验"）

学完本项目 = 入门 Agent 工程师；有完整项目 + 开源贡献 = 可面试

## 学习建议

1. **不要跳课**：阶段 1-3 是地基（手写原理），跳过会导致后面似懂非懂
2. **闭卷毕业考**：每个阶段的毕业考必须从空文件开始写，写完跑通才算真懂
3. **卡住超 30 分钟**：立刻问（把代码 + 报错 + 你的理解贴给 AI 助手）
4. **写学习笔记**：每阶段记录 3 个核心概念 + 1 个踩坑经验
5. **做真实项目**：学完阶段 3 就可以做"个人笔记 RAG"，学完阶段 7 就可以做"公司知识库问答"

## 贡献指南

欢迎提交 Issue 和 Pull Request：

- 🐛 发现 bug 或文档错误
- 💡 改进代码示例（更清晰的注释、更好的错误处理）
- 📚 补充学习资源（博客、视频、论文）
- 🎯 分享你的毕业考项目（作为示例）

## 许可证

MIT License - 可自由用于学习和商业项目。

---

**开始你的 Agent 开发之旅吧！** 从阶段 1 的 `01_LLM/学习手册.md` 开始，一步一个脚印 🚀
