# Agent 学习路线图

> 给 Java 后端的 Agent 学习地图。你已完成阶段 1-2,本图规划阶段 3-7。
> 用法:**每个新阶段开始前,让 ZCode 按本图生成该阶段的详细手册**(像 01/02 那样,目标/代码/自测/毕业考齐全),自己敲完找 ZCode 验收。
> 阶段 3 的手册已经生成好:[03_rag/学习手册.md](03_rag/学习手册.md)。

---

## 你现在的位置

- **阶段 1 ✅ 裸调 LLM API**:messages 协议、多轮对话、流式输出、历史窗口裁剪、会话存盘、JSON 结构化输出(毕业考 `06_my_chat.py` 已通过)
- **阶段 2 ✅ 手写 Agent**:`tools` JSON Schema、`tool_calls` 点菜、`role=tool` 喂回、`名字→函数` 调度表、`MAX_STEPS` 防失控、完整 Agent 循环(毕业考 `03_my_agent.py` 已通过,5 个工具含 2 个自设计)
- **环境现状**:本机全局 Python 3.10.6,`openai` / `python-dotenv` / `pydantic` / `numpy` 已装好,直接 `python 文件名.py` 即可;`.env` 统一放仓库根目录一份(`load_dotenv()` 会自动向上层找),模板已建好,填上 Key 就能用

## 学习原则(承袭前两阶段,全程不变)

1. **先手写后框架**:阶段 3-6 不用任何 Agent 框架,把框架的"黑盒"亲手拆一遍;阶段 7 才用 Spring AI,那时你会知道框架替你做了什么
2. **Java 视角**:每个新概念都配 Java 类比(注解反射、中间件、Spring 容器……)
3. **闭卷毕业考**:每阶段最后一课,不看手册从空文件重写,写完跑通才算毕业
4. **卡住超 30 分钟**:代码 + 完整报错 + 你跑的原话,一起贴给 ZCode

## 路线总览

| 阶段 | 目录 | 主题 | 回答的核心问题 | 毕业标准 | 预估 |
|---|---|---|---|---|---|
| 3 | `03_rag/` | RAG 与上下文工程 | 怎么让 Agent "读过你的文档"?历史太长怎么裁? | 闭卷写出笔记问答 mini RAG | ~1.5 周 |
| 4 | `04_engineering/` | Agent 工程化 | 脚本怎么变成能测试、能扩展的项目? | 装饰器注册工具 + 结构化输出 + 单测的模块化 Agent | ~2 周 |
| 5 | `05_mcp/` | MCP 协议 | 工具怎么变成"任何 Agent 都能插"的标准件? | 手写 MCP server + 你的 Agent 动态发现工具 | ~1 周 |
| 6 | `06_multi_agent/` | 工作流与多 Agent | 一个 Agent 什么都能干 = 什么都干不好,怎么编排? | 手写 router / orchestrator-workers / 反思循环 | ~1.5 周 |
| 7 | `07_java_spring_ai/` | **Java 落地 · Spring AI** | 概念全通之后,回到你的生产栈 | Spring Boot 发布带 RAG + 工具调用的 Agent 服务 | ~3 周 |

> 预估按"每晚 1-1.5 小时"算,总共 2-3 个月。快慢无所谓,**每阶段的毕业考必须闭卷**。

---

## 阶段 3 · RAG 与上下文工程(手册已就绪,今天就能开始)

模型的知识停在训练那天,而且上下文窗口装不下你的全部资料。RAG(检索增强生成)的思路:**先从你的文档里检索出最相关的几段,塞进 prompt,再让模型回答**。同时正式解决阶段 2 毕业考留的进阶题——带工具调用的历史怎么裁。

课表(8 课 + 毕业考,全部在 [03_rag/学习手册.md](03_rag/学习手册.md)):

1. `00_embedding.py` — 文字变成向量(embedding API)
2. `01_similarity.py` — 手写余弦相似度,纯 Python 排序
3. `02_vector_store.py` — 60 行手写你的第一个"向量数据库"(含 JSON 持久化)
4. `03_chunking.py` — 长文档切块:固定滑窗 vs 按标题切
5. `04_rag_chat.py` — 整合:**能"读过你笔记"的聊天机器人**,回答带来源引用
6. `05_context_trim.py` — 上下文工程:token 预算 + 按"完整轮次"裁剪 + 混合压缩
7. `06_query_rewrite.py` — 检索优化第一招:先改写问题,再检索
8. `07_rerank.py` — Rerank 精排:粗筛 top-10 → 打分重排 → top-3
9. 毕业考 `08_my_rag_agent.py`(闭卷):把 RAG 做成 Agent 的一个工具(agentic RAG),模型自己决定查不查

**注意**:DeepSeek 没有 embedding 接口,向量要走智谱(或 SiliconFlow),根目录 `.env` 里配两组变量——手册第 0 课有模板。

## 阶段 4 · Agent 工程化:从脚本到项目

你现在的 Agent 是一个 300 行脚本。真项目里它要能加工具不改核心、能校验模型输出、能不花 token 就跑测试。这一阶段把阶段 2 的 Agent 重构成规范的 Python 项目——用的全是你在 Spring 里享受过的思想。

课表(手册已就绪:[04_engineering/学习手册.md](04_engineering/学习手册.md)):

1. 项目拆分:`llm_client.py` / `tools.py` / `agent.py` / `main.py` 四模块
2. **装饰器工具注册器**:`@tool` 注解 + `inspect` 反射,自动生成 JSON Schema、自动注册——Java 视角就是"注解 + 反射扫描"
3. RAG 工具化:阶段 3 的手写检索变成一个普通 `@tool`(懒加载 + 带来源返回)
4. Pydantic 结构化输出 + 校验失败自动重试(Java:Jackson + Bean Validation)
5. ReAct 提示词模式(Thought/Action/Observation),和 function calling 对比
6. 流式 Agent:边想边说 + `[工具]` 卡片
7. pytest 单测:mock 掉 LLM,0 token 跑测试

```python
@tool
def read_file(path: str) -> str:
    """读取指定文件的全部文本内容"""
    ...
# 一行注解,Schema 和注册表自动生成——你写 Spring 时天天享受的就是这个
```

毕业考:闭卷把阶段 3 的毕业 Agent 重构成"装饰器注册 + Pydantic 输出 + pytest mock 单测"的四模块项目——agentic RAG 在阶段 3 毕业考已经体验过,本阶段专攻工程质量。

## 阶段 5 · MCP:工具的 USB-C

你写的工具只有你的 Agent 能用。MCP(Model Context Protocol)把"工具"变成标准件:任何 MCP 客户端都能发现并调用你发布的工具。Java 后端看它就是熟悉的"标准化中间件/驱动"思维。

课表预告:

1. 协议概览:host / client / server 三角色,tools / resources / prompts 三原语
2. 用官方 SDK 手写 MCP server(stdio 传输):把阶段 2 的文件工具搬上去
3. 手写 MCP client 接进你的 Agent:**动态发现工具,告别硬编码 `TOOL_IMPLS`**
4. 把阶段 3 的 RAG 知识库发布成 MCP server
5. 现成生态一览与安全边界(工具权限、prompt 注入)

毕业考:你的 Agent 启动时通过 MCP 动态加载至少 3 个工具,一个都不在代码里硬编码。

## 阶段 6 · 工作流与多 Agent 编排

单 Agent 上下文越堆越长、工具越挂越乱。Anthropic《Building Effective Agents》里的五种模式全部手写落地:

1. 五模式图解:prompt chaining / routing / parallelization / orchestrator-workers / evaluator-optimizer
2. 手写 **router**:按问题类型分发到不同"专家" Agent
3. 手写 **orchestrator-workers**:主管拆任务 → worker 并行执行 → 汇总
4. 手写 **evaluator-optimizer**:写代码 → 评审 → 改,循环到过关
5. 成本与延迟账本:什么时候坚决不用多 Agent(大多数时候)

毕业考:手写一个"研究小队"(规划 → 并行搜集 → 汇总成报告)。

## 阶段 7 · 回主场:Java + Spring AI

概念全通之后,回到你的生产栈。选型:**Spring AI 为主**(Spring 生态一脉、Spring Boot 3.x 无缝、官方支持 MCP),LangChain4j 为备选(风格更像 LangChain,课程里一课概览即可)。要求 JDK 17+。

课表预告:

1. 环境搭建 + 第一个 `ChatClient` 调用(对照阶段 1:概念一模一样)
2. `@Tool` 工具调用:框架自动完成"点菜→反射执行→回传"——**就是你阶段 2 手写的 `agent_reply` + `run_tool_calls`**
3. 结构化输出(entity 映射,对照你的 Pydantic 课)
4. ChatMemory 与 Advisor(对照你的 messages 列表和窗口裁剪)
5. RAG:`TokenTextSplitter` + `VectorStore`(SimpleVectorStore 起步 → **PGVector,你熟悉的 PostgreSQL 装个插件**)
6. MCP client / server 的 Java 版(阶段 5 的概念直接复用)
7. Spring Boot + SSE 把 Agent 发布成 HTTP 流式服务(Controller/Service,你的主场)
8. 观测:日志 + actuator,进阶 Langfuse 链路追踪

```java
@Tool(description = "读取指定文件的全部文本内容")
public String readFile(String path) { ... }

// ChatClient 自动完成整个工具调用循环——阶段 2 你手写过的每一行都在里面
```

**毕业项目**:「企业知识库问答服务」——Spring Boot + Spring AI + PGVector + MCP 工具 + SSE 流式接口,一个能写进简历、能在公司落地的项目。

## 为什么这么排(针对你这个 Java 后端)

1. **生态顺序**:Agent 领域的新概念几乎都先在 Python 生态出现,阶段 3-6 用最小成本建立概念(每个概念都标注 Java 对应物),阶段 7 一次性搬到 Java,学两遍 = 牢固一遍
2. **工作场景全覆盖**:知识库问答(RAG)、工具调用、结构化输出,正是 Java 后端接 AI 需求最集中的三件事
3. **协议思维是你的强项**:MCP 之于工具,就像 JDBC 之于数据库、SPI 之于插件——阶段 5 的理解会直接迁移到阶段 7 的 Spring AI MCP

## 毕业之后(生产化方向,按需再开)

- **评测**:建题库跑批 + LLM-as-judge(Agent 版的单元测试/回归测试)
- **可观测**:全链路 trace(每次调用、每轮工具、token 花费)
- **安全**:prompt 注入防护、工具最小权限、输出过滤
- **多模态 / 微调**:什么时候真的需要(多数场景是"从来不需要")

## 进度追踪

- [x] 阶段 1 · 裸调 LLM API
- [x] 阶段 2 · 手写 Agent(function calling)
- [x] 阶段 3 · RAG 与上下文工程
- [ ] 阶段 4 · Agent 工程化 ← **你在这里**
- [ ] 阶段 5 · MCP 协议
- [ ] 阶段 6 · 工作流与多 Agent
- [ ] 阶段 7 · Java + Spring AI(含毕业项目)
