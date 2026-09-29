# 开源 Agent 源码学习手册

> **定位**：本文是 [ROADMAP.md](ROADMAP.md) 阶段 7 之后的**第二主线**——阶段 1-6 教「手写原理」，本文教「读懂生产级实现」。
>
> **适用前提**：已完成阶段 0-6（裸调 API / 手写 Agent / RAG / 工程化 / MCP / 多 Agent）。
> **目标**：把读到的架构能力，变成求职面试时能讲清的**设计取舍**。
>
> **数据来源**：本文所有行数、文件路径、设计点均来自 **2026-09-29 本地实测**（`git clone --depth 1` + 逐文件计数 + 源码阅读），不是网上转述。

---

## 第 0 章｜先想清三件事

### 0.1 源码学习只能补一类能力

Agent 工程能力分三层，**只有中间那层能靠读源码补**：

| 层 | 内容 | 你从哪获得 | 读源码有用吗 |
|---|---|---|---|
| **原理层** | Agent 循环、tool calling、RAG 流程 | 阶段 1-3 手写 | ❌ 无用，你已会 |
| **架构层** | 上下文治理、状态边界、持久化、恢复 | **尚未获得** | ✅ **源码的唯一价值** |
| **护栏层** | 并发隔离、超时重试、成本账本、评测 | **尚未获得** | ⚠️ 只能看个大概，必须项目里真踩 |

**推论**：读源码要盯**架构层**。去读原理层的实现是浪费时间——你已经有更好的学习版本（自己写的）。

### 0.2 仓库体量决定成败

实测数据（GitHub API，2026-09-29）：

| 仓库 | Star | 体积 | 判断 |
|---|---|---|---|
| `langchain-ai/langchain` | 147k | **589 MB** | ❌ 永不通读 |
| `langchain-ai/langgraph` | 42k | **514 MB** | ⚠️ 只读 `checkpoint` 单模块 |
| `OpenHands/OpenHands` | 89k | 427 MB | ⚠️ 只看架构 |
| `crewAIInc/crewAI` | 59k | 288 MB | ⚠️ 只看架构 |
| **`HKUDS/nanobot`** | 48k | 67 MB（浅克隆 19.7 MB） | ✅ **主教材**（但有噪音，见第 1 章） |
| `modelcontextprotocol/python-sdk` | 24k | **16 MB** | ✅ 热身 |
| `langchain-ai/open_deep_research` | 12.7k | 6.6 MB | ❌ **已归档**，不再迭代 |

**硬规则**：一个仓库如果不能在 1 个周末看到全貌，就**不要以"通读"为目标**，改成"定点查证"。

### 0.3 什么叫"读懂了"

三问自检，答不上来就是没读懂：

1. 如果让我删掉这个模块自己写，我会在哪一步卡住？
2. 这个设计如果换掉，会在什么场景下出问题？
3. 我能否举出**我的项目里**会用到它的具体场景？

第 3 问答不上来 → **这个模块现在不该读**。

---

## 第 1 章｜主教材实测地图：nanobot

### 1.1 先纠正一个流传的错误数字

网上说「nanobot 约 4000 行代码」。**实测是错的，差了 36 倍**：

```
nanobot/ 包内：424 个 Python 文件、144,799 行
  ├─ channels/（52 个聊天平台适配器）  61,601 行  ← 噪音，禁止阅读
  ├─ tests/  （包内测试）              35,230 行  ← 噪音，禁止阅读
  ├─ webui/  （网页控制台）            17,987 行  ← 噪音，禁止阅读
  └─ 核心（agent/session/providers…）  65,211 行  ← 真正的教材
```

（`nanobot/` 包内另有 361 个仓库级 `tests/` 文件、105,611 行，同样与学习目标无关。）

**这本身就是第一课**：生产级 Agent 项目里，**约 79% 的代码是渠道适配、测试和 UI，不是 Agent 能力**
（(61,601 + 35,230 + 17,987) ÷ 144,799 ≈ 79%；即使只算渠道 + UI 也有 55%）。
面试时能说出这句话，比背任何框架 API 都有说服力。

### 1.2 核心阅读路线（9 个文件，11,659 行）

按优先级排序——**不是按目录顺序**：

| 优先级 | 文件 | 行数 | 学习目标 | 对照你的 |
|---|---|---|---|---|
| ★★★ | `agent/runner.py` | 1,305 | 工具调用执行循环（共享给多种 agent） | [02_agent/02_simple_agent.py](02_agent/02_simple_agent.py) |
| ★★★ | `agent/context_governance.py` | 892 | **上下文治理与压缩**（最高价值） | [03_rag/03_context_window.py](03_rag/03_context_window.py) |
| ★★★ | `agent/autocompact.py` | 117 | 空闲会话的**主动**压缩 | 无（你没有这个概念） |
| ★★★ | `session/manager.py` | 1,663 | 会话持久化 + 摘要检查点提交 | [04_engineering/](04_engineering/) |
| ★★★ | `session/summary.py` | **46** | **全仓库最高信息密度** | 无 |
| ★★ | `agent/memory.py` | 1,185 | 记忆归档 + `Consolidator` 合并 | [03_rag/](03_rag/) |
| ★★ | `session/recovery.py` | 865 | 中断恢复 + 副作用安全 | 无 |
| ★★ | `agent/loop.py` | 2,388 | 顶层主循环 | [02_agent/04_graduation.py](02_agent/04_graduation.py) |
| ★ | `utils/gitstore.py` | ~520 | 用 git 做记忆版本控制 | 无 |
| ★ | `agent/tools/mcp.py` | 1,509 | MCP 集成 | [05_mcp/](05_mcp/) |

**核心路线（★★★ + ★★）= 8,344 行**，配 5 周。★ 为可选。

**禁止阅读**：`channels/`（61,601 行）、`tests/`（35,230 行）、`webui/`（17,987 行）。

---

## 第 2 章｜5 个必读设计（含真实代码与面试话术）

> 这一章是整本手册的核心。每个设计都按「**朴素做法 → 它怎么做 → 为什么聪明 → 面试怎么讲**」四段展开。
> 你要能在不看资料的情况下复述这 5 个设计。

### 设计 1｜摘要检查点：用一条隐藏消息做压缩边界

**朴素做法**（很可能就是你 [03_rag/03_context_window.py](03_rag/03_context_window.py) 的写法）：
"保留最近 N 轮 + 把更早的总结成一段"。**这个做法有个死结：边界会漂移。**
第二次压缩时，你分不清"哪些内容已经被总结过"——容易重复总结，或者漏掉。

**它怎么做**（`session/summary.py` 全文只有 46 行）：

```python
SUMMARY_CONTINUATION_TEXT = "Continue the active task from the working-memory checkpoint above."

def is_summary_checkpoint(message) -> bool:
    """Identify the durable boundary of a replacement summary."""
    return (
        is_hidden_history_message(message)
        and message.get("content") == SUMMARY_CONTINUATION_TEXT
    )
```

配上 `session/manager.py` 的 `commit_summary_checkpoint()`：把摘要文本写进 session metadata（`_last_summary`），**同时**在历史里插一条隐藏的 continuation 消息当标记；恢复时只要找到这条标记，就知道"标记之前是摘要，之后是原始记录"。

**为什么聪明**：压缩点从"靠位置推断"变成**靠标记识别**，于是压缩是**幂等且可重放的**。第二次、第三次压缩都不会算错边界。

**面试怎么讲**：
> "很多人的上下文压缩就是'留最近 N 轮 + 总结前面的'，这在**多轮压缩**时会出错，因为边界不可识别。nanobot 的做法是插入一条隐藏的 continuation 消息作为持久边界标记，让压缩幂等化。区别在于：前者只在单次压缩时正确，后者可以反复压缩。"

---

### 设计 2｜H / delta：区分"已被模型接受的输入"和"还没发出去的增量"

**朴素做法**：每次请求都把完整历史重新拼一遍。
**问题**：无法判断"我这次改了历史，到底改了已发送的部分还是只改了增量"，压缩会误伤；有些 provider 支持对话状态复用，你也没法配合。

**它怎么做**（`agent/context_governance.py`）：

```python
@dataclass(slots=True)
class ContextCompactionState:
    """Track accepted provider input H separately from the unsent delta."""

    raw_messages: list[dict[str, Any]]          # 完整原始历史
    accepted_messages: list[dict[str, Any]]     # 已被 provider 接受的部分（H）
    raw_accepted_boundary: int                  # H 与 delta 的边界
    active_summary: str | None
    summary_transcript_builder: SummaryTranscriptBuilder
    consolidate_history: HistoryConsolidator
    summary_checkpoint: SessionSummaryCheckpoint | None = None
```

**另一条同样重要的约束**——模块 docstring 明确写了：

> *"It may return copied messages or persisted-result placeholders, **but it must not mutate an existing session history list in place**."*

**为什么聪明**：上下文压缩最难的不是"怎么压"，而是"**压了之后，哪些已经发出去的、哪些还没发的**"。不区分这两者，压缩就会破坏 provider 侧的对话状态。而"不许原地修改历史"这条约束，把并发场景下的数据竞争从设计层面消掉了。

**面试怎么讲**：
> "上下文治理真正的难点是状态边界，不是压缩算法。要把'已被模型接受的输入'和'未发送的增量'分开跟踪，否则压缩会破坏 provider 侧状态。另外这个模块有条硬约束——禁止原地修改 session history，只能返回副本，这是用不可变设计消掉并发问题。"

---

### 设计 3｜主动压缩：在空闲时压缩，而不是等上下文爆了

**朴素做法**：等 token 快满了才压缩（被动、在关键路径上、增加延迟）。
**它怎么做**（`agent/autocompact.py`）：

```python
"""Auto compact: proactive compression of idle sessions to reduce token cost and latency."""
```

按 session TTL 扫描**空闲会话**，在后台调度归档与压缩；并且会跳过有 in-flight 任务的会话：

```python
def check_expired(self, schedule_background, resolve_runtime, active_session_keys=()) -> None:
    """Schedule archival for idle sessions, skipping those with in-flight agent tasks."""
```

还有一处防御性细节值得学——`_is_expired()` 遇到无法解析的时间戳时**返回 False 而不是抛异常**，注释写着：

> *"an unusable value must not escape the idle scan and stop the agent loop."*

**为什么聪明**：把压缩成本从**用户可感知的关键路径**挪到**空闲时间**。这是"延迟优化"的经典手法迁移到 LLM 场景。

**面试怎么讲**：
> "上下文压缩不要放在请求关键路径上。nanobot 用会话 TTL 扫描空闲会话，在后台提前压缩，把成本挪出用户可感知路径。还有个小细节很体现功力：扫描时间戳解析失败时返回 False 而不是抛异常，因为一条脏数据不该让整个 agent loop 停下来。"

---

### 设计 4｜恢复的副作用安全：判断一个中断的 tool call 能否重放

**朴素做法**：失败了就整个重跑。
**问题**：重放一个**有副作用的**工具调用（发消息、改文件、下单）可能造成重复副作用。

**它怎么做**（`session/recovery.py`）：

> *"Durable, side-effect-safe recovery for interrupted WebUI turns."*
> *"Checkpoint materialization is a session operation shared with AgentLoop lifecycle boundaries, so **transport code never has to guess whether an interrupted tool call is safe to replay**."*

配合 `context_governance.py` 里对畸形 tool call 的防御：

```python
"""... a degenerate call with ``name=None`` / ``""`` cannot be executed
and is rejected by upstream APIs if replayed."""
```

**为什么聪明**：把"能否重放"的判断**收拢到一个地方**（session 层），而不是让每个调用方自己猜。这是"把决策集中、把复杂度关进一个模块"的典型。

**面试怎么讲**：
> "任务恢复的难点不是'怎么续跑'，而是'**哪些步骤能安全重放**'。有副作用的工具调用重放会产生重复副作用。nanobot 把 checkpoint 物化做成 session 层的共享操作，让传输层不需要猜某个中断的调用能不能重放——把判断收拢到一处。"

---

### 设计 5｜用 Git 给记忆做版本控制

**朴素做法**：记忆存 JSON，直接覆盖写。
**问题**：模型把记忆写坏了，没法回滚，也看不到演进过程。

**它怎么做**（`utils/gitstore.py`）：

```python
"""Git-backed version control for memory files, using dulwich."""
```

用纯 Python 的 git 实现 `dulwich`，提供 `auto_commit()` / `log()` / `diff_commits()` / `revert()`。
配合 `agent/memory.py` 的 docstring：*"Memory storage, transcript archiving, and session checkpoint consolidation."*——注意 **consolidation（合并）** 而非 append（追加）。

**为什么聪明**：记忆是**会写坏的状态**。给它加上版本控制，就同时得到了审计（log）、回滚（revert）、和调试能力（diff）。而且用 dulwich 而不是调 git 命令，没有外部依赖。

**面试怎么讲**：
> "长期记忆是会写坏的状态，所以要给它版本控制。nanobot 用 dulwich 把记忆文件做成 git 仓库，这样天然获得了审计、diff 和回滚能力。另一个容易忽略的点是它的记忆是 consolidation 而不是 append——合并比追加难得多，但避免记忆无限膨胀。"

---

## 第 3 章｜5 周阅读计划

> 节奏：每天 1-1.5 小时。**每周有验收标准（Exit），不达标不进下一周。**

### 第 0 周｜热身：python-sdk 通读（16 MB，最小）

| 项 | 内容 |
|---|---|
| 读什么 | `modelcontextprotocol/python-sdk` 全文（只有 16 MB，能读完） |
| 带着的问题 | 我手写的 [05_mcp/file_server.py](05_mcp/file_server.py) 和它差在哪？协议层替我处理了哪些我没想到的边界？ |
| 做什么 | 用它重写你 MCP server 里的一个工具注册 |
| Exit | 能说出"协议层替我处理了 3 件我没想到的事" |
| 产出 | `notes/源码头测-python-sdk.md` |

### 第 1 周｜工具执行循环：`runner.py` + `loop.py`

| 项 | 内容 |
|---|---|
| 读什么 | `agent/runner.py`(1,305) → `agent/loop.py`(2,388) |
| 怎么读 | **调用链追踪**：从入口开始跟一条完整请求穿过所有层，画成图（手画，别截图） |
| 重点看 | runner 如何被多种 agent 共享？工具执行的错误处理在哪一层？ |
| Exit | 能合上屏幕口述主循环，并说出与你 [02_agent/04_graduation.py](02_agent/04_graduation.py) 的 2 个设计差异 |
| 产出 | `notes/nanobot-循环与工具.md` |

### 第 2 周｜上下文治理 ★最高价值

| 项 | 内容 |
|---|---|
| 读什么 | `agent/context_governance.py`(892) + `agent/autocompact.py`(117) |
| 怎么读 | **删掉重写再 diff**：关掉源码，自己实现一遍 H/delta 边界跟踪，再对比 |
| 重点看 | `ContextGovernanceConfig` 的字段为什么是这些？`CONTEXT_SAFETY_BUFFER` 为什么是 1024？ |
| Exit | 你的项目里**真的加上**了 H/delta 边界或主动压缩，有前后对比数据（token 数 / 延迟） |
| 产出 | `notes/nanobot-上下文治理.md` + 项目里一次真实改动 |

> **本周是整条路线的价值峰值。** 上下文工程是阶段 1-6 从没训练过的能力——你的玩具跑不到 10 万 token，所以你根本不知道自己的压缩策略是错的。

### 第 3 周｜会话与记忆：`session/` + `memory.py`

| 项 | 内容 |
|---|---|
| 读什么 | `session/summary.py`(46) → `session/manager.py`(1,663) → `agent/memory.py`(1,185) |
| 怎么读 | 从 46 行的 `summary.py` 切入（最高信息密度），再顺着 `is_summary_checkpoint` 的调用点展开 |
| 重点看 | `commit_summary_checkpoint()` 怎么写 metadata？`Consolidator` 怎么合并？ |
| Exit | 你的项目实现了摘要检查点，且能演示"连续压缩两次不出错" |
| 产出 | `notes/nanobot-会话与记忆.md` |

### 第 4 周｜恢复与安全：`recovery.py`

| 项 | 内容 |
|---|---|
| 读什么 | `session/recovery.py`(865) + `utils/gitstore.py`(~520) |
| 怎么读 | **定点查证**：只回答"哪些步骤能安全重放""恢复时怎么不重复执行副作用" |
| 做什么 | 给项目加"任务失败可续跑"，记录改前后指标（重跑耗时、重复花费） |
| Exit | 项目里能演示：任务中途杀掉进程，重启后接着跑，且副作用不重复 |
| 产出 | `notes/nanobot-恢复机制.md` |

### 第 5 周｜定点爆破 LangGraph + 补评测

| 项 | 内容 |
|---|---|
| 前提 | LangGraph **必须已有真实需求**（要中断、要人工审批后继续）。没有就只做评测 |
| 读什么 | LangGraph **仅** `checkpoint` 相关模块（严禁通读 514 MB） |
| 做什么 | ① 用 LangGraph 重写项目一个流程节点，实现中断 → 人工确认 → 继续<br>② 补 eval：5-10 个用例 + LLM-as-judge |
| Exit | ① 能回答"状态存哪、用什么键隔离、怎么保证不重复执行副作用"<br>② 有一份可复跑的评测报告，能看到改一版 prompt 后的分数变化 |
| 产出 | `notes/langgraph-checkpoint.md`、`notes/评测与护栏.md` |

> **评测（eval）是把"项目驱动"从自我安慰变成真实学习的前提。** 没有它，你改 prompt 全靠体感——而"体感"恰恰是阶段 1-6 没教过你的东西。

---

## 第 4 章｜阅读方法（三种，按强度排序）

| 方法 | 做法 | 用在 |
|---|---|---|
| **删掉重写再 diff** | 关掉源码自己实现同一功能，然后对比 | 第 2 周（必用） |
| **调用链追踪** | 从入口跟一条完整请求穿过所有层，画成图 | 第 1 周 |
| **定点查证** | 只带一个问题进去，找到答案就出来 | 第 4、5 周 |

**禁止**：从头到尾顺序读文件。这是最低效、最容易自我感动的方式。

### 每次阅读必须留下的四句话

模板见 [notes/源码头测模板.md](notes/源码头测模板.md)：

```markdown
**它的问题**：它在这个模块要解决什么？（一句话，不许抄 README）
**它的设计**：怎么做？（数据结构 + 关键流程，手画图）
**为什么比我的好**：和我阶段的实现比好在哪？（我认为我的更好也要写理由）
**我改了什么**：我在自己项目里动了哪一处？（没改 = 这次学习无效）
```

**最后一项是硬性约束**：没有落到自己项目上的源码学习，不计入进度。

---

## 第 5 章｜面试问题库（直接由上面的设计导出）

> 面试官问的从来不是"你看过什么"，而是**"你遇到什么问题、怎么权衡的"**。
> 下面每题都能用第 2 章的设计作答。

**Q1. 长对话上下文你怎么处理？**
> 答：分层——近期保留原文，远期摘要化，工具结果做归一化。关键是压缩要**幂等**：我用隐藏的边界标记识别压缩点，而不是靠位置推断，这样连续压缩多次不会算错边界。

**Q2. 上下文压缩放在请求关键路径上吗？**
> 答：不放。应该在空闲时提前压——我按会话 TTL 扫描空闲会话后台压缩，把成本挪出用户可感知路径。同时跳过有 in-flight 任务的会话。

**Q3. Agent 任务跑到一半崩了怎么办？**
> 答：分两步。先判断**哪些步骤能安全重放**——有副作用的工具调用重放会产生重复副作用；然后把"能否重放"的判断收拢到统一的一层，不要让每个调用方自己猜。

**Q4. 工具返回的超长内容怎么处理？**
> 答：做内容归一化 + 持久化占位——超长工具结果不直接塞进上下文，而是落盘、上下文里放引用。同时要防御畸形 tool call（比如 name 为空的退化调用），否则重放时会被上游 API 拒绝。

**Q5. 长期记忆怎么存？**
> 答：当成**会写坏的状态**来存。我给记忆加版本控制（git 语义），天然获得审计、diff 和回滚。另外记忆应该是 consolidation 而不是 append，否则会无限膨胀。

**Q6. 你读过哪些开源实现？它为什么那么设计？**
> 答：（用第 2 章任意一个设计作答，重点讲**取舍**而不是功能）

---

## 第 6 章｜进度追踪

| 周 | 主题 | 状态 | 产出 |
|---|---|---|---|
| 0 | 热身：python-sdk 通读 | ⬜ | |
| 1 | 工具执行循环 `runner.py` + `loop.py` | ⬜ | |
| 2 | 上下文治理 `context_governance.py` ★ | ⬜ | |
| 3 | 会话与记忆 `session/` + `memory.py` | ⬜ | |
| 4 | 恢复与安全 `recovery.py` | ⬜ | |
| 5 | LangGraph checkpoint（触发式）+ 评测 | ⬜ | |

### 完成判据（自检）

**源码侧**
- [ ] `python-sdk` 完整读完，能说出协议层替你处理的 3 件事
- [ ] 第 2 章的 5 个设计，能在不看资料的前提下复述
- [ ] 至少 1 个模块做过「删掉重写再 diff」
- [ ] `notes/` 下至少 5 份符合四句话模板的记录

**项目侧**
- [ ] 上下文策略有实测前后对比数据（token / 延迟）
- [ ] 任务可中断、可续跑，副作用不重复，有演示证据
- [ ] 有可复跑的评测脚本 + 一份分数报告

**求职侧**
- [ ] 第 5 章的 6 个问题能脱口而出
- [ ] 备好 5 个「难点 + 权衡」故事（不是功能介绍，是**取舍**）
- [ ] 3 篇技术文章发布

---

## 附录｜本地源码与当前状态

| 项 | 状态 |
|---|---|
| `D:\python\projectCode\_oss-reference\nanobot\` | ✅ 已就绪（浅克隆 19.7 MB） |
| `D:\python\projectCode\_oss-reference\open-swe\` | ❌ 未获取（github.com:443 被重置，三次失败）。需要时用代理重试 |
| 本手册数据 | 全部为 2026-09-29 实测 |

> **关于 open-swe**：本手册未依赖它。第 1-4 周全部围绕 nanobot；open-swe 只在"想看另一个异步 agent 的持久化实现"时作为补充。
