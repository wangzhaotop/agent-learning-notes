# agent-learning-notes
使用 Python 学习并构建 AI Agent 的项目,包含学习笔记与代码实践。路线图见 [ROADMAP.md](ROADMAP.md)。

## 学习路线

| 阶段 | 目录 | 主题 | 状态 |
|---|---|---|---|
| 0 | `00_python基础/` | Python 基础(专题 5-9 补强) | 手册已就绪 |
| 1 | `01_LLM/` | 裸调 LLM API | ✅ 已毕业 |
| 2 | `02_agent/` | 手写 Agent(function calling) | ✅ 已毕业 |
| 3 | `03_rag/` | RAG 与上下文工程 | ✅ 已毕业 |
| 4 | `04_engineering/` | Agent 工程化(装饰器注册/Pydantic/单测) | ✅ 已完成 7 课 + 21 个单测(毕业考 `/summary` 待闭卷) |
| 5 | `05_mcp/` | MCP 协议(含异步补课) | ✅ 已毕业 |
| 6 | `06_multi_agent/` | 工作流与多 Agent 编排 | 手册已就绪 |
| 7 | `07_java_spring_ai/` | Java 落地 · Spring AI(毕业项目) | 待开始 |

每个目录里有一份「学习手册.md」:目标 → 带注释代码 → 自测题 → 闭卷毕业考。

## 运行环境

- 解释器:conda 环境 `agent`(`D:\Anaconda3\envs\agent\python.exe`,Python 3.11)
- 依赖:`openai` / `python-dotenv` / `pydantic` / `pytest` / `mcp`
- 跑程序:`python main.py`;跑测试:`python -m pytest tests -v`(必须带 `-m`)
