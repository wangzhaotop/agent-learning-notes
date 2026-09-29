# Agent 开发完整学习路线（Python 版）

> **学习周期**：2-3 个月（每天 1-1.5 小时）  
> **目标人群**：有 Python 基础，想系统学习 AI Agent 开发的工程师  
> **核心理念**：先手写后框架，从原理到生产，从单 Agent 到多 Agent

---

## 总览

本路线图分为 **7 个阶段**，每个阶段都有完整的学习手册 + 带注释代码 + 自测题 + 闭卷毕业考。

```
阶段 0：Python 基础补强（可选）
   ↓
阶段 1：裸调 LLM API（理解 messages、流式、JSON mode）
   ↓
阶段 2：手写 Agent（tool calling、ReAct 循环）
   ↓
阶段 3：RAG 与上下文工程（向量检索、切块、窗口管理）
   ↓
阶段 4：Agent 工程化（装饰器、Pydantic、单元测试）
   ↓
阶段 5：MCP 协议（Model Context Protocol 实战）
   ↓
阶段 6：多 Agent 编排（链式、路由、并行、orchestrator）
   ↓
阶段 7：生产化部署（FastAPI、Milvus、mem0、可观测）
```

---

## 阶段 0：Python 基础补强（可选，1 周）

**适合人群**：Python 基础薄弱，或对装饰器/迭代器/异步不熟悉的同学。

### 学习内容

1. **函数进阶**：位置参数、关键字参数、*args、**kwargs、返回值
2. **容器操作**：列表推导、字典操作、集合去重
3. **面向对象 OOP**：类定义、继承、`__init__`、`__str__`
4. **高阶函数**：闭包、装饰器（阶段 4 会大量使用）
5. **迭代器与生成器**：`yield`、`next()`、自定义迭代器
6. **错误处理**：try/except、自定义异常
7. **文件操作**：读写文件、with 上下文管理器
8. **异步编程基础**：async/await（阶段 5 MCP 会用到）

### 毕业标准

- 能手写装饰器（如 `@timer` 计时装饰器）
- 能手写生成器（如斐波那契数列生成器）
- 理解异步的基本概念（能看懂 `async def` / `await`）

### 资源推荐

- 《Python Cookbook》第 7-9 章
- Real Python 的 Decorators / Iterators / Async 系列文章

---

## 阶段 1：裸调 LLM API（1 周）

**核心问题**：不用任何框架，直接调用 LLM API，理解 messages 结构、流式输出、JSON mode。

### 学习目标

1. 理解 LLM API 的 messages 结构（system / user / assistant）
2. 掌握流式输出（`stream=True`），逐 token 打印
3. 掌握 JSON mode（`response_format={"type": "json_object"}`）
4. 理解 token 计费原理、temperature 参数

### 课表（4 课 + 1 毕业考）

| 课次 | 文件 | 主题 | 时间 |
|------|------|------|------|
| 1 | `01_simple_chat.py` | 单轮对话 | 30 分钟 |
| 2 | `02_streaming.py` | 流式输出 | 30 分钟 |
| 3 | `03_json_mode.py` | JSON 结构化输出 | 60 分钟 |
| 毕业 | `04_graduation.py` | 多轮对话 + 历史管理 | 90 分钟 |

### 毕业考要求

闭卷手写一个**命令行聊天机器人**：
- 支持多轮对话（保存历史 messages）
- 支持流式输出（逐字打印）
- 支持命令（`/clear` 清空历史、`/save` 保存对话、`/exit` 退出）
- 历史记录持久化到本地文件（JSON 格式）

---

## 阶段 2：手写 Agent（1-2 周）

**核心问题**：什么是 Agent？如何让 LLM 自己决定调用工具？ReAct 循环怎么实现？

### 学习目标

1. 理解 function calling / tool use 协议
2. 手写 Agent 循环（while 循环 + tool_calls 判断）
3. 理解 ReAct 模式（Reasoning + Acting）
4. 实现多工具 Agent（给 Agent 3 个以上工具）

### 课表（3 课 + 1 毕业考）

| 课次 | 文件 | 主题 | 时间 |
|------|------|------|------|
| 1 | `01_function_calling.py` | function calling 基础 | 60 分钟 |
| 2 | `02_simple_agent.py` | 手写 Agent 循环 | 90 分钟 |
| 3 | `03_react_agent.py` | ReAct 模式 | 60 分钟 |
| 毕业 | `04_graduation.py` | 多工具 Agent | 120 分钟 |

### 毕业考要求

闭卷手写一个**多工具 Agent**，至少包含 3 个工具：
- `get_weather(city)`：查询天气
- `search_web(query)`：搜索网络
- `calculator(expression)`：计算器

要求：
- Agent 能根据用户问题自主选择调用哪个工具
- 支持多步推理（如"北京明天下雨吗？"需要先查天气，再判断）
- 打印完整的推理链路（Thought → Action → Observation）

---

## 阶段 3：RAG 与上下文工程（2 周）

**核心问题**：如何让 Agent 读取外部知识？RAG 的完整流程是什么？上下文窗口满了怎么办？

### 学习目标

1. 理解 RAG 的离线流程（文档加载 → 切块 → 向量化 → 存储）
2. 理解 RAG 的在线流程（用户提问 → 向量检索 → 拼接 prompt → LLM 回答）
3. 掌握切块策略（按字符、按句子、重叠切块）
4. 掌握上下文窗口管理（滑动窗口、摘要压缩）
5. 手写一个简单的向量数据库（用 chromadb）

### 课表（3 课 + 1 毕业考）

| 课次 | 文件 | 主题 | 时间 |
|------|------|------|------|
| 1 | `01_simple_rag.py` | 简单 RAG | 90 分钟 |
| 2 | `02_chunking.py` | 切块策略 | 60 分钟 |
| 3 | `03_context_window.py` | 窗口管理 | 90 分钟 |
| 毕业 | `04_rag_agent.py` | 完整 RAG Agent | 180 分钟 |

### 毕业考要求

闭卷手写一个**完整的 RAG Agent**：
- 知识库：准备 5-10 份文档（你的工作文档 / 笔记 / 博客）
- 离线处理：文档切块 → 向量化 → 存入 chromadb
- 在线查询：用户提问 → 检索 top-3 相关文档 → 拼接 prompt → LLM 回答
- 引用来源：回答时标注来自哪份文档（如"根据《Python 手册》第 3 章..."）

要求：
- 支持重新加载知识库（`/reload` 命令）
- 支持调整检索参数（top-k、相似度阈值）
- 打印检索到的文档片段（方便调试）

---

## 阶段 4：Agent 工程化（1-2 周）

**核心问题**：如何让 Agent 代码更模块化、可测试、易扩展？

### 学习目标

1. 用装饰器实现工具注册器（`@tool` 装饰器）
2. 用 Pydantic 校验工具参数和返回值
3. 用 pytest 写单元测试（测试工具、Agent 推理链路）
4. 模块化设计（tools.py、agent.py、llm_client.py、main.py）
5. 错误处理与日志记录

### 课表（7 课 + 21 个单测 + 1 毕业考）

| 课次 | 文件 | 主题 | 时间 |
|------|------|------|------|
| 1-7 | 各模块 | 装饰器、Pydantic、单测 | 每课 60-90 分钟 |
| 毕业 | `/summary` 命令 | 闭卷实现命令 | 120 分钟 |

### 毕业考要求

闭卷实现 `/summary` 命令，要求：
- 分析当前对话历史，生成摘要
- 用 Pydantic 定义摘要结构（主题、关键点、待办事项）
- 写 3 个单元测试覆盖边界情况

---

## 阶段 5：MCP 协议（1 周）

**核心问题**：什么是 MCP（Model Context Protocol）？如何自定义 MCP server？

### 学习目标

1. 理解 MCP 协议的设计理念（工具连接的标准化）
2. 手写一个 MCP file server（文件读写工具）
3. 手写一个 MCP RAG server（知识库检索工具）
4. Agent 通过 MCP client 调用远程工具
5. 异步编程补课（MCP 基于 asyncio）

### 课表（5 课 + 1 毕业考）

| 课次 | 文件 | 主题 | 时间 |
|------|------|------|------|
| 1 | `async_lab.py` | 异步编程补课 | 60 分钟 |
| 2 | `file_server.py` | MCP file server | 90 分钟 |
| 3 | `rag_server.py` | MCP RAG server | 90 分钟 |
| 4 | `client.py` | MCP client | 60 分钟 |
| 毕业 | `agent_main.py` | MCP Agent | 120 分钟 |

### 毕业考要求

闭卷手写一个**MCP Agent**，通过 MCP 调用本地 server 的工具：
- 启动 2 个 MCP server（file + RAG）
- Agent 能自动选择调用哪个 server 的工具
- 支持跨 server 的多步推理（如"读取 data.txt，然后在知识库里搜索相关内容"）

---

## 阶段 6：多 Agent 编排（1-2 周）

**核心问题**：多个 Agent 如何协作？四大编排模式是什么？

### 学习目标

1. **链式（Sequential）**：Agent A → Agent B → Agent C 顺序执行
2. **路由（Router）**：根据问题类型，路由到不同的专家 Agent
3. **并行（Parallel）**：多个 Agent 同时执行，汇总结果
4. **orchestrator-workers**：主管 Agent 分配任务给工人 Agent

### 课表（4 课 + 1 毕业考）

| 课次 | 文件 | 主题 | 时间 |
|------|------|------|------|
| 1 | `01_chain.py` | 链式编排 | 60 分钟 |
| 2 | `02_router.py` | 路由分发 | 90 分钟 |
| 3 | `03_parallel.py` | 并行执行 | 90 分钟 |
| 4 | `04_orchestrator.py` | orchestrator-workers | 120 分钟 |
| 毕业 | 研究小队项目 | 闭卷多 Agent | 180 分钟 |

### 毕业考要求

闭卷手写一个**研究小队 Agent**：
- **主管 Agent**：接收研究主题，规划子任务
- **搜集 Agent**（3 个）：并行搜索不同来源（网络、知识库、学术数据库）
- **汇总 Agent**：整合所有信息，生成研究报告

要求：
- 用 orchestrator-workers 模式
- 主管能根据搜集结果动态调整计划
- 最终输出 Markdown 格式的研究报告

---

## 阶段 7：生产化部署（2-3 周，核心阶段）

**核心问题**：如何把 Agent 部署成生产服务？企业需要哪些额外能力？

### 学习目标

1. **Instructor**：结构化输出 + 自动重试（替代手动 JSON 解析）
2. **mem0**：长期记忆管理（跨会话记住用户偏好）
3. **FastAPI**：HTTP 服务化 + SSE 流式响应
4. **Milvus**：生产级向量数据库（替代 chromadb）
5. **LangSmith / Langfuse**：可观测（链路追踪、token 成本分析）
6. **LLM-as-judge**：自动评测 Agent 质量
7. **OpenAI Swarm / Claude SDK**：企业级 Agent 框架快速上手

### 课表（7 课 + 1 毕业考）

| 课次 | 文件 | 主题 | 时间 |
|------|------|------|------|
| 0 | `概念.md` | 生产化 vs Demo 的区别 | 30 分钟阅读 |
| 1 | `01_instructor.py` | Instructor 结构化输出 | 60 分钟 |
| 2 | `02_mem0_memory.py` | mem0 长期记忆 | 90 分钟 |
| 3 | `03_fastapi_agent.py` | FastAPI 服务化 + SSE | 90 分钟 |
| 4 | `04_milvus_rag.py` | Milvus 向量数据库 | 90 分钟 |
| 5 | `05_observability.py` | 可观测（LangSmith / Langfuse） | 60 分钟 |
| 6 | `06_evaluation.py` | 评测（LLM-as-judge） | 90 分钟 |
| 7 | `07_swarm_intro.py` | OpenAI Swarm 快速上手 | 60 分钟 |
| 毕业 | `08_knowledge_service.py` | 企业知识库问答服务 | 180 分钟 |

### 毕业考要求（8 项全部达标）

闭卷手写一个**企业知识库问答服务**：

1. **FastAPI 服务**：提供 `/chat`（非流式）、`/chat/stream`（流式）、`/health` 接口
2. **Milvus 向量库**：启动时从 `knowledge/` 文件夹加载文档
3. **mem0 长期记忆**：记住用户偏好（如"我是 Python 开发者"）
4. **Instructor 结构化输出**：返回 `{answer, confidence, sources}` 结构
5. **可观测日志**：记录每次请求的 token、延迟、检索文档数
6. **工具调用**：至少 2 个工具（知识库检索 + 其他）
7. **错误处理**：Milvus 连接失败、LLM 超时，都有降级策略
8. **评测**：写 5 个测试用例，LLM-as-judge 打分平均 >= 7/10

---

## 学习原则（贯穿全程）

### 1. 先手写后框架

- **阶段 1-3**：手写所有核心逻辑（Agent 循环、向量检索、上下文管理）
- **阶段 4-7**：用成熟工具（Instructor、mem0、Milvus、FastAPI）
- **收益**：框架会更新，但原理不会变；遇到问题能快速定位

### 2. 闭卷毕业考

- 每个阶段的毕业考必须**从空文件开始写**，不看之前的代码
- 写完跑通才算毕业，否则重做
- 卡住超 30 分钟立刻问（贴代码 + 报错 + 你的理解）

### 3. 真实项目驱动

- **阶段 3 毕业后**：做"个人笔记 RAG"（你的博客 / 工作文档）
- **阶段 7 毕业后**：做"公司知识库问答"（改成你公司的真实需求）
- **简历项目**：把毕业考项目改成完整的可部署服务

---

## 毕业后去哪

完成全部 7 个阶段后，你具备了**企业 Agent 开发的完整技能栈**。

### 下一步方向

1. **LangGraph 深入**（可选）：
   - 企业常用的复杂工作流框架（状态机 + 检查点 + Human-in-the-Loop）
   - 推荐：LangGraph 官方教程 + 手写一个"审批工作流 Agent"

2. **多模态 Agent**（前沿）：
   - 图片理解（GPT-4V / Claude with vision）
   - 语音输入输出（Whisper + TTS）
   - 视频分析（帧提取 + 批量图片理解）

3. **企业落地实战**（核心竞争力）：
   - **成本优化**：小模型做路由/分类，大模型做关键决策
   - **安全合规**：prompt injection 防御、敏感信息脱敏
   - **A/B 测试**：对比不同 prompt / 模型的效果
   - **用户反馈闭环**：收集点赞/点踩，用 Few-shot 优化

4. **开源贡献**（简历加分）：
   - 给 LangChain / mem0 / MCP 提 PR
   - 发布你的 Agent 项目到 GitHub
   - 写技术博客（3-5 篇深度文章）

---

## 技能树总结

```
Agent 开发完整技能树（7 个阶段）
│
├─ 阶段 1：裸调 LLM API
│  └─ messages、流式、JSON mode、token 计费
│
├─ 阶段 2：手写 Agent
│  └─ function calling、ReAct 循环、多工具编排
│
├─ 阶段 3：RAG 与上下文工程
│  └─ 向量检索、切块、窗口管理、摘要压缩
│
├─ 阶段 4：工程化
│  └─ 装饰器、Pydantic、pytest、模块化设计
│
├─ 阶段 5：MCP 协议
│  └─ MCP server/client、异步编程、工具标准化
│
├─ 阶段 6：多 Agent 编排
│  └─ 链式、路由、并行、orchestrator-workers
│
└─ 阶段 7：生产化部署（核心）
   ├─ Instructor（结构化输出 + 自动重试）
   ├─ mem0（长期记忆管理）
   ├─ FastAPI（服务化 + SSE 流式）
   ├─ Milvus（生产级向量库）
   ├─ LangSmith / Langfuse（可观测）
   ├─ LLM-as-judge（自动评测）
   └─ Swarm / Claude SDK（企业框架）
```

---

## 时间规划建议

| 阶段 | 预估时间 | 累计时间 | 里程碑 |
|------|---------|---------|--------|
| 0 | 1 周（可选） | 1 周 | Python 基础达标 |
| 1 | 1 周 | 2 周 | 能裸调 LLM API |
| 2 | 1-2 周 | 3-4 周 | 手写 Agent 循环 |
| 3 | 2 周 | 5-6 周 | 理解 RAG 完整流程 |
| 4 | 1-2 周 | 7-8 周 | 代码工程化达标 |
| 5 | 1 周 | 8-9 周 | 理解 MCP 协议 |
| 6 | 1-2 周 | 10-11 周 | 掌握多 Agent 编排 |
| 7 | 2-3 周 | **12-14 周** | **可面试 Agent 工程师** |

**每天投入 1-1.5 小时，3 个月完成全部 7 阶段。**

---

## 常见问题

### 1. 必须按顺序学吗？

**是的**。阶段 1-3 是地基（手写原理），跳过会导致后面似懂非懂。阶段 4-7 是在地基上盖房子。

### 2. 学完能达到什么水平？

- **入门级 Agent 工程师**：能独立开发完整的 Agent 项目
- **简历项目**：有 2-3 个可部署的 Agent 服务（阶段 3、6、7 的毕业考）
- **面试能力**：能讲清楚 Agent 原理、RAG 流程、多 Agent 编排、生产化部署

### 3. 和培训班 / 训练营的区别？

| 维度 | 培训班 | 本路线图 |
|------|--------|---------|
| 深度 | 浅（主要调库） | 深（手写原理 + 框架） |
| 时间 | 1-2 个月速成 | 3 个月扎实 |
| 成本 | 几千到几万元 | 免费 |
| 项目 | 统一的 demo 项目 | 真实需求改造（你的笔记/公司文档） |

### 4. 需要 GPU 吗？

**不需要**。全程调用 API（DeepSeek / 智谱 / OpenAI），本地只跑推理逻辑。

### 5. 推荐用哪个 LLM API？

- **国内**：DeepSeek（便宜）、智谱 GLM（功能全）、Kimi（长文本）
- **国外**：OpenAI（贵但稳定）、Claude（推理能力强）
- **建议**：学习用 DeepSeek（成本低），生产用 GPT-4 / Claude（质量高）

---

**开始你的 Agent 开发之旅吧！** 从阶段 1 的 `01_LLM/学习手册.md` 开始 🚀
