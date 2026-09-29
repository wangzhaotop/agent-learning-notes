# mini-coding-agent 逐行导读

> **源码位置**：`D:\python\projectCode\mini-coding-agent\`
> **规模**：`mini_coding_agent.py` **1019 行**（含注释与空行）/ **916 行**（非空行）+ 测试 **308 行**
> **作者**：Sebastian Raschka（《Build a Large Language Model (From Scratch)》作者）
> **本文配套**：[READING_PLAN.md](../READING_PLAN.md) 第二主线——阶段 1-6 教你「手写原理」，这里教你「读生产级 harness」
>
> 本文所有行号均经**本地实测核对**（脚本逐条断言），可直接对照阅读。

---

## 第 0 章｜速查

### 0.1 行号导航表

| 行范围 | 内容 | 组件归属 |
|---|---|---|
| 1–48 | import、常量（`MAX_TOOL_OUTPUT=4000` 第 34 行、`MAX_HISTORY=12000` 第 35 行） | — |
| **39–47** | **六组件索引注释**（作者给的阅读地图，先读它） | — |
| 49–71 | 工具函数 `now()` / `clip()` / `middle()` | 组件 4 |
| **73–143** | `class WorkspaceContext`(75) + `.build()`(86) + `.text()`(125) | **组件 1** |
| **146–165** | `class SessionStore`(146)，`save`(154) / `load`(159) / `latest`(162) | **组件 5** |
| 167–177 | `class FakeModelClient`(167) | 测试缝 |
| 179–223 | `class OllamaModelClient`(179)，`complete`(187) | 模型接入 |
| **225–280** | `class MiniAgent`(225)，`__init__`(226) / `from_session`(261) / `remember`(271) | 主干 |
| **282–328** | `build_tools()`(282)，delegate 注册在第 321–327 行 | **组件 3** |
| **333–374** | `build_prefix()`(333)，风险文案在第 337 行 | **组件 2** ★ |
| 376–388 | `memory_text()`(376) | 组件 5 |
| **390–420** | `history_text()`(390)，`recent_start` 在第 397 行 | **组件 4** ★ |
| **422–431** | `prompt()`(422) | **组件 2** ★ |
| 433–443 | `record()`(433) / `note_tool()`(437) | 组件 5 |
| **445–494** | `ask()`(445) ← **主循环** | 主干 |
| 496–515 | `run_tool()`(496)（五道检查） | 组件 3 |
| 517–522 | `repeated_tool_call()`(517)，判定在第 521 行 | 组件 3 |
| 524–534 | `tool_example()`(524) | 组件 3 |
| 536–600 | `validate_tool()`(536) | 组件 3 |
| 602–614 | `approve()`(602) | 组件 3 |
| 616–715 | `parse()`(616) / `retry_notice()`(650) / `parse_xml_tool()`(662) / `extract()`(692) | 解析层 |
| 717–740 | `reset()`(717) / `path_is_within_root()`(722) / `path()`(734) | 组件 3 |
| 742–867 | 六个 `tool_*` 实现（`list_files` 742 … `tool_delegate` 847） | 组件 3 |
| **847–867** | `tool_delegate()`(847)，子 agent `read_only=True` 在第 862 行 | **组件 6** |
| 869–910 | `build_welcome()`(869) | 展示 |
| 912–943 | `build_agent()`(912) | 装配 |
| 945–967 | `build_arg_parser()`(945) | CLI |
| 969–1019 | `main()`(969) / REPL | 入口 |

### 0.2 先跑起来（不动代码）

```powershell
# 1) 看它的依赖: 零第三方依赖,只需 Python 3.10+
cd D:\python\projectCode\mini-coding-agent
python mini_coding_agent.py --help

# 2) 完整跑起来需要 Ollama（唯一前置）
#    https://ollama.com/download
ollama serve                      # 另开一个终端
ollama pull qwen3.5:4b
python mini_coding_agent.py --cwd . --approval ask
```

**先读代码还是先跑？** 先跑。你要先看到它"真的能改文件"，再回头看实现才有意义。

> ⚠️ `--approval auto` 会允许模型任意执行命令和写文件，**只在你信任的仓库和 prompt 下用**。

---

## 第 1 章｜先看骨架：一次请求的完整生命周期

这是全文件的主动脉。读懂这条线，剩下的都是细节。

```
main()  ──► build_agent()  ──► WorkspaceContext.build()   ← 组件1:采集工作区事实
   │              │            SessionStore(...)          ← 组件5:会话存储
   │              │            OllamaModelClient(...)     ← 模型客户端
   │              └──► MiniAgent.__init__()               (226)
   │                     ├─ build_tools()                 ← 组件3:工具白名单+风险标记
   │                     ├─ build_prefix()                ← 组件2:静态前缀(只算一次!)★
   │                     │    self.tools  = build_tools()      (256)
   │                     │    self.prefix = build_prefix()     (257)
   │                     └─ session_store.save()          ← 组件5:立刻落盘
   │
   └──► agent.ask(user_message)                            (445)
            │
            ├─ record({"role":"user",...})    ← 先记录,再循环
            │
            └─ while tool_steps < max_steps:  ← 主循环 (445-494)
                 │
                 ├─ prompt(user_message)      ← 组件2+4+5 合成   (422)
                 │     = prefix              (静态, 可缓存)
                 │     + memory_text()       (精简工作记忆)
                 │     + history_text()      (削减后的转录)
                 │     + 当前请求
                 │
                 ├─ model_client.complete(prompt, max_new_tokens)
                 │
                 ├─ parse(raw) ──► "tool" │ "retry" │ "final"    (616)
                 │
                 ├─ 若 tool:  run_tool() ─► validate ─► repeated? ─► approve ─► 执行 ─► record
                 │            tool_steps += 1, continue
                 ├─ 若 retry: record 一条 runtime notice, continue（不消耗 tool_steps）
                 └─ 若 final: record 并 return
```

**三个必须看懂的设计**：

1. **`prefix` 在 `__init__` 里只算一次**（第 257 行），循环里只拼可变部分 → 这是 prompt caching 能省钱的前提
2. **`tool_steps` 和 `attempts` 是两个独立计数器**（都在 `ask()` 内）→ 模型胡言乱语不会把工具预算吃光
3. **每一步都 `record()` 落盘**（第 433 行）→ 进程被杀也能恢复

---

## 第 2 章｜六组件精读（附自问自答）

### 组件 1｜Live Repo Context（第 73–143 行）

**它干什么**：在对话开始前，把工作区的"稳定事实"一次性采集好，作为 prompt 前缀的一部分。

```python
DOC_NAMES = ("AGENTS.md", "README.md", "pyproject.toml", "package.json")   # 第 14 行
```

`WorkspaceContext.build()`（第 86 行）内部有个 `git()` 小函数，调 `git rev-parse` / `branch` / `status` / `log --oneline -5`，**每个都带 fallback 和 5 秒超时**：

```python
def git(args, fallback=""):
    try:
        result = subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                                text=True, check=True, timeout=5)
        return result.stdout.strip() or fallback
    except Exception:
        return fallback
```

**读的时候问自己**：
- 为什么要采集 `default_branch` 而不只是 `branch`？
- `project_docs` 为什么只截取 **1200 字符**（第 113 行）？不截会怎样？
- 每个 `git` 调用失败都有 fallback → 这个项目能在一个**不是 git 仓库**的目录里跑吗？

**面试话术**：
> "工具的上下文注入要区分'稳定事实'和'每轮变化'。仓库结构、分支、近期提交这些在一次会话里基本不变，所以采集一次进前缀，让 prompt caching 能命中。反过来，如果每轮都重新采集，前缀就一直在变，缓存全废。"

---

### 组件 2｜Prompt Shape & Cache Reuse（第 333–374、422–431 行）★最高价值

**这是全文件最值钱的一段。** 先看它是怎么拼 prompt 的：

```python
def prompt(self, user_message):            # 第 422 行
    return "\n\n".join([
        self.prefix,                        # 静态:规则+工具表+示例+工作区事实
        self.memory_text(),                 # 半静态:任务/文件/笔记
        "Transcript:\n" + self.history_text(),
        "Current user request:\n" + user_message,
    ])
```

而 `self.prefix` 是在 `__init__` 里**只构建一次**的（第 **257** 行；`self.tools` 在 256 行）。

`build_prefix()`（第 333 行）的拼接顺序，注意它的**排列是有讲究的**：

```
1. 角色声明        "You are Mini-Coding-Agent..."
2. Rules          15 条行为规则
3. Tools          工具表（名/参数/风险/描述）
4. Examples       有效的响应样例
5. workspace.text()  工作区事实       ← 在第 5 位,不是第 1 位
```

**读的时候问自己**：
- 为什么 `workspace.text()` 放在**最后**而不是最前面？（提示：缓存命中是按前缀长度算的）
- 第 337 行 `risk = "approval required" if tool["risky"] else "safe"` —— 把风险信息写进 prompt 有什么用？
- `build_prefix()` 里塞了 5 个 `examples`，这些样例是在教模型什么格式？

**面试话术**（这段最值钱，务必背熟）：
> "Prompt 要按'变化频率'分层：静态部分（角色、规则、工具表、样例）放最前面且只构建一次，半静态部分（工作记忆）居中，每轮变化的转录和用户输入放最后。这样放是因为 **prompt caching 按前缀匹配**——前缀一变，后面全部重新计算。很多人的实现每次请求都把 system prompt 重新拼一遍，字符串拼接本身不贵，但**缓存命中率变成 0** 才是真花钱的地方。"

---

### 组件 3｜Structured Tools, Validation & Permissions（第 282–328、496–614、717–867 行）

**它干什么**：模型只能通过具名工具行动，且每个工具要过五道关。

工具表本身就是一个数据结构（第 282 行）：

```python
tools = {
    "list_files": {"schema": {"path": "str='.'"}, "risky": False, "description": ..., "run": self.tool_list_files},
    "read_file":  {"schema": {"path": "str", "start": "int=1", "end": "int=200"}, "risky": False, ...},
    "search":     {...},                                    "risky": False,
    "run_shell":  {...},                                    "risky": True,     # ←
    "write_file": {...},                                    "risky": True,     # ←
    "patch_file": {...},                                    "risky": True,     # ←
}
if self.depth < self.max_depth:                             # 第 321 行
    tools["delegate"] = {...}                               # 第 322 行:子 agent 才拿得到 delegate
```

注意 `schema` 用的是**字符串描述**（`"str='.'"`、`"int=200"`）而不是 JSON Schema——因为这是给**文本模型**看的，不是给原生 function calling 用的。

**核心：`run_tool()` 的五道检查**（第 496 行），顺序不能换：

```python
def run_tool(self, name, args):
    tool = self.tools.get(name)
    if tool is None:                      return f"error: unknown tool '{name}'"      # 1 白名单
    try: self.validate_tool(name, args)
    except Exception as exc:              return "error: invalid arguments..."        # 2 参数校验
    if self.repeated_tool_call(...):      return "error: repeated identical tool call" # 3 防死循环
    if tool["risky"] and not self.approve(name, args):
                                          return f"error: approval denied for {name}" # 4 审批门
    try: return clip(tool["run"](args))
    except Exception as exc:              return f"error: tool {name} failed: {exc}"   # 5 兜底
```

**为什么"校验必须在审批之前"**——测试里专门验证了这一点：

```python
def test_invalid_risky_tool_does_not_prompt_for_approval(tmp_path):   # tests 第 168 行
```

**也就是说：参数都不合法的调用，不该弹窗打扰用户。** 这个顺序是安全 + 体验的双重考量。

再看两个安全设计：

**① 路径逃逸防护**（第 722 行）——不是简单的字符串前缀比较：

```python
def path_is_within_root(self, resolved):
    probe = resolved
    while not probe.exists() and probe.parent != probe:   # 一路向上找到存在的祖先
        probe = probe.parent
    for candidate in (probe, *probe.parents):
        try:
            if candidate.samefile(self.root):             # 用 samefile 比 inode → 能挡符号链接
                return True
        except OSError:
            continue
    return False
```

测试覆盖了三种情况（tests 第 192 / 199 / 213 行）：
- `test_path_rejects_parent_escape`（`../` 逃逸）
- `test_path_rejects_symlink_escape`（**符号链接**逃逸——字符串比较挡不住，`samefile` 能挡）
- `test_path_accepts_case_variant_on_case_insensitive_filesystems`（Windows 大小写不敏感）

**② 精确替换**（第 828 行 `tool_patch_file`）——`old_text` 必须**恰好出现 1 次**：

```python
count = text.count(old_text)
if count != 1:
    raise ValueError(f"old_text must occur exactly once, found {count}")
```

**读的时候问自己**：
- `repeated_tool_call()` 为什么只看**最近两次**（第 521 行 `tool_events[-2:]`）而不是全部历史？
- `validate_tool` 里 `read_file` 为什么要校验 `start < 1 or end < start`？
- 为什么工具失败返回**字符串错误**而不是抛异常给主循环？（提示：错误要进上下文给模型看）

**面试话术**：
> "工具层要做五件事且顺序有讲究：白名单、参数校验、重复调用检测、风险审批、异常兜底。关键是**校验必须在审批之前**——参数都不合法的调用不该弹窗打扰用户。另外安全上不能用字符串前缀比较判断路径是否越界，符号链接能绕过；正确做法是 `samefile` 比 inode，并且一路向上找到存在的祖先再比。"

---

### 组件 4｜Context Reduction & Output Management（第 390–420 行）★最高价值

**这是最能体现"生产经验"的一段。** 全部逻辑在 `history_text()` 这 30 行里：

```python
MAX_TOOL_OUTPUT = 4000     # 第 34 行
MAX_HISTORY = 12000        # 第 35 行

def history_text(self):                                                     # 第 390 行
    history = self.session["history"]
    if not history:
        return "- empty"

    lines = []
    seen_reads = set()
    recent_start = max(0, len(history) - 6)     # 第 397 行 ← 最近 6 条算 "recent"
    for index, item in enumerate(history):
        recent = index >= recent_start

        # 规则A: 写过这个文件 → 把它从"已读"集合里移除（内容已变，缓存失效）
        if item["role"] == "tool" and item["name"] in ("write_file", "patch_file"):
            path = str(item["args"].get("path", ""))
            seen_reads.discard(path)

        # 规则B: 非 recent 的重复读文件 → 直接跳过，不进上下文
        if item["role"] == "tool" and item["name"] == "read_file" and not recent:
            path = str(item["args"].get("path", ""))
            if path in seen_reads:
                continue
            seen_reads.add(path)

        # 规则C: recent 给 900 字符，旧的只给 180/220 字符
        if item["role"] == "tool":
            limit = 900 if recent else 180
            lines.append(f"[tool:{item['name']}] {json.dumps(item['args'], sort_keys=True)}")
            lines.append(clip(item["content"], limit))
        else:
            limit = 900 if recent else 220
            lines.append(f"[{item['role']}] {clip(item['content'], limit)}")

    return clip("\n".join(lines), MAX_HISTORY)       # 整体再兜一次 12000
```

**三层削减，层层递进**：

| 层 | 手段 | 解决的问题 |
|---|---|---|
| 单条 | `clip(text, 4000)` | 一个工具返回 10 万字符会把上下文炸掉 |
| 时间衰减 | recent 给 900，旧的给 180/220 | 越早的内容信息密度越低 |
| 去重 | `seen_reads` + **写操作使其失效** | 同一个文件读 5 遍，上下文里只留最新一份 |
| 总量 | 整体 `clip(..., 12000)` | 最后兜底 |

**规则A 是最精妙的一处**：写过文件之后，前面读到的旧内容就**过期了**，必须从"已读"集合里移除，否则后续再读同一文件会被误判为重复而跳过，模型就会拿着过期内容工作。

测试专门锁定了这个行为（tests 第 302 / 342 行）：

```python
def test_history_text_deduplicates_reads_but_not_after_write(tmp_path)
def test_history_text_deduplicates_unchanged_repeated_reads(tmp_path)
```

**读的时候问自己**：
- 为什么 `recent` 的界限是 **6 条**？（不是 5 也不是 10）
- 去重只对 `read_file` 做，为什么不对 `run_shell` 做？（提示：同样命令的返回一定一样吗？）
- `clip()` 的截断信息 `...[truncated N chars]` 为什么要写进上下文？

**面试话术**（这是最能打的一段）：
> "上下文削减要分层做：单条结果裁剪、按时间衰减分配预算、重复内容去重、总量兜底。最容易做错的是**去重的失效逻辑**——如果模型写过这个文件，前面读到的内容就过期了，必须让去重缓存失效，否则模型会拿着旧版本干活。另一个细节是截断时要**显式告诉模型'这里被截了 N 个字符'**，否则它会以为看到的就是全部。"

---

### 组件 5｜Transcripts, Memory & Resumption（第 146–165、376–388、433–443 行）

**双轨状态**：全量 transcript（可恢复）+ 精简 working memory（进 prompt）。

```python
# 全量:落盘 JSON,一条不丢
class SessionStore:                          # 第 146 行
    def save(self, session):                 # 第 154 行
        path.write_text(json.dumps(session, indent=2), encoding="utf-8")
    def latest(self):                        # 第 162 行:按 mtime 找最新
        files = sorted(self.root.glob("*.json"), key=lambda p: p.stat().st_mtime)

# 精简:只留三个桶 + 固定长度
@staticmethod
def remember(bucket, item, limit):           # 第 271 行
    if item in bucket: bucket.remove(item)   # 先移除
    bucket.append(item)                      # 再追加 → 天然变成 LRU
    del bucket[:-limit]                      # 只保留最后 limit 个
```

会话结构（第 248–253 行）：

```python
{
  "id": "20260401-144025-2dd0aa",     # 时间戳+随机后缀
  "created_at": ..., "workspace_root": ...,
  "history": [],                       # 第 253 行:全量转录
  "memory": {"task": "", "files": [], "notes": []},   # 三个桶
}
```

三个桶各有容量（`note_tool`，第 437 行）：

```python
self.remember(memory["files"], str(path), 8)    # 最近 8 个文件
self.remember(memory["notes"], note, 5)         # 最近 5 条笔记(每条 clip 到 220 字符)
memory["task"] = clip(user_message.strip(), 300) # 任务只记第一次(第 447 行 if not memory["task"])
```

**为什么 `task` 只在第一次设**——这是"任务锚点"：多轮之后模型容易跑偏，把最初的任务固定保留，能把它拉回来。

**读的时候问自己**：
- `"history"` 和 `"memory"` 为什么不合并成一个？（提示：一个要完整可重放，一个要小）
- 为什么 `ask()` 第一步就 `record()` 用户消息，而不是等模型回复后再一起记？
- `SessionStore` 直接把会话 JSON 存在**被操作的仓库里**（`.mini-coding-agent/sessions/`），有什么好处和风险？

**面试话术**：
> "会话状态要分两轨：一份全量 transcript 用于恢复和审计，一份精简 working memory 用于进 prompt。working memory 用固定容量的桶（任务锚点、近期文件、关键笔记），配合 LRU 式更新。任务锚点只在第一轮写入——它是防止多轮跑偏的锚。"

---

### 组件 6｜Delegation & Bounded Subagents（第 847–867 行）

**子 agent 不是"再起一个 agent"，而是"起一个受约束的 agent"**：

```python
def tool_delegate(self, args):                # 第 847 行
    if self.depth >= self.max_depth:
        raise ValueError("delegate depth exceeded")
    task = str(args.get("task", "")).strip()
    if not task:
        raise ValueError("task must not be empty")
    child = MiniAgent(
        model_client=self.model_client,
        workspace=self.workspace,
        session_store=self.session_store,
        approval_policy="never",      # ← 子 agent 永远不能获批危险操作
        max_steps=int(args.get("max_steps", 3)),   # ← 默认只给 3 步
        max_new_tokens=self.max_new_tokens,
        depth=self.depth + 1,         # ← 深度+1
        max_depth=self.max_depth,     # ← 默认 max_depth=1 → 只能一层
        read_only=True,               # 第 862 行 ← 只读
    )
    child.session["memory"]["task"] = task
    child.session["memory"]["notes"] = [clip(self.history_text(), 300)]  # ← 继承 300 字符上下文
    return "delegate_result:\n" + child.ask(task)
```

**四重边界，缺一不可**：

| 边界 | 实现 | 防什么 |
|---|---|---|
| 深度 | `depth + 1` vs `max_depth=1` | 无限递归 |
| 权限 | `approval_policy="never"` + `read_only=True`（第 862 行） | 子 agent 乱写乱执行 |
| 预算 | `max_steps=3` 默认 | 子 agent 烧光 token |
| 上下文 | `notes = [clip(history, 300)]` | 上下文爆炸式传递 |

**读的时候问自己**：
- 为什么子 agent 只拿到 **300 字符**的父上下文，而不是完整 history？
- `tools["delegate"]` 的 `risky` 标记是 `False`（第 324 行）——但子 agent 明明可能做危险事，为什么标 False？（提示：看子 agent 的 `read_only`）
- `tools["delegate"]` 只在 `depth < max_depth` 时才注册（第 321–327 行）——这跟 `validate_tool` 里的检查是不是重复了？

**面试话术**：
> "子 agent 的关键不是'能不能起'，而是'边界在哪'。要同时限制四件事：递归深度、工具权限（子 agent 一律只读 + 从不自动批准）、步数预算、以及传给它的上下文大小。很多人的多 agent 实现只限制了深度，结果子 agent 拿着全量上下文和写权限，一次委派就把成本和风险都放大了。"

---

## 第 3 章｜练习阶梯（从改一行到重构）

### L1｜换模型客户端（30 分钟）★建议第一个做

**目标**：把 Ollama 换成你 `.env` 里已有的 DeepSeek。

- 参考 `OllamaModelClient`（第 179–223 行），它用 `urllib` POST 到 `/api/generate`
- 你需要写一个 `OpenAICompatClient`，POST 到 `/chat/completions`
- **注意**：Ollama 的 `/api/generate` 是**裸 prompt 进、裸文本出**；而 `/chat/completions` 是 `messages` 数组进、结构出。你要处理这个不匹配

**验收**：`python mini_coding_agent.py --cwd . "列出当前目录"` 能跑通

**为什么值得做**：这一步让你彻底看清"agent 和模型是解耦的"——`MiniAgent` 只依赖 `complete(prompt, max_new_tokens) -> str` 这一个接口。

---

### L2｜给削减加上"可观测"（1 小时）

**目标**：现在削减是静默的，你不知道省了多少。

- 在 `history_text()`（第 390 行）里统计：原始字符数 / 削减后字符数 / 跳过了几条重复读
- 加一个 `/stats` 命令（参考 `main()` 里 `/memory` 的分支，第 969 行之后的 REPL 段）

**验收**：跑一轮多步任务后，能说出"这次省了 X%"

**为什么值得做**：这是把"体感"变成"数据"的第一步，也是面试时能说"我实测过"的底气。

---

### L3｜删掉重写组件 4（半天）★核心练习

**目标**：关掉源码，自己实现 `history_text()`。

1. 先通读第 390–420 行，理解三层削减 + 写后失效
2. **关掉文件**，从空白开始写一个 `my_history_text()`
3. 打开源码 diff，回答：我漏了哪一层？写后失效我想到了吗？
4. 用仓库自带测试验证：`python -m pytest tests/ -q`

**验收**：`test_history_text_deduplicates_reads_but_not_after_write` 和 `test_history_text_deduplicates_unchanged_repeated_reads` 两个测试通过

**为什么值得做**：这就是 [READING_PLAN.md](../READING_PLAN.md) 第 3 章讲的「删掉重写再 diff」，最强的主动阅读法。

---

### L4｜加一个缺失的能力（1 天）

选一个（都有明确验收）：

| 选项 | 要做的事 | 验收 |
|---|---|---|
| A. 会话级 token 预算 | 累计 token 超限时强制压缩历史 | 长会话不再无限增长 |
| B. 工具结果落盘 | 超大结果写文件，上下文只留引用（对照 nanobot 的做法） | 10 万字符的工具输出不炸上下文 |
| C. 中断恢复 | 进程被杀后 `--resume latest` 能接着跑完 | 有演示证据 |

**对照资源**：B 和 C 可以去 `D:\python\projectCode\_oss-reference\nanobot\` 看生产实现（`agent/context_governance.py`、`session/recovery.py`）

---

### L5｜写测试（半天）

这份代码有 19 个测试（`tests/test_mini_coding_agent.py`，308 行），覆盖了：

```
✓ 工具→final 基本流程          ✓ XML 风格 write_file
✓ 空输出重试                   ✓ 畸形 tool payload 重试
✓ 重试不消耗工具预算           ✓ 会话保存与恢复
✓ 子 agent 委派                ✓ patch_file 精确匹配
✓ 非法危险工具不弹审批         ✓ list_files 隐藏内部状态
✓ 路径拒绝 ../ 逃逸            ✓ 路径拒绝符号链接逃逸
✓ Windows 大小写不敏感         ✓ 重复相同调用被拒
✓ 欢迎界面长路径不破框         ✓ prompt 顶层段落对齐
✓ history 去重 + 写后失效      ✓ 重复未变读去重
✓ Ollama 客户端 payload 正确
```

**练习**：给它加一个测试，覆盖你自己在 L4 里加的能力。

**面试价值**：能说出"这个项目 916 行主代码配 308 行测试，我加了一个测试覆盖 X"——比说"我读过源码"强太多。

---

## 第 4 章｜读完这本，下一本读什么

### `huggingface/smolagents`（官方生产库）

- **实测**：`src/smolagents/agents.py` **1,813 行**（README 宣称 `<1000 行`，指的是纯代码行）
- **为什么接着读它**：同一个问题，看生产库怎么做成**可扩展抽象**
  - 它把 agent 分成 `CodeAgent`（动作写成 Python 代码）和 `ToolCallingAgent`（动作写成 JSON）
  - 它的核心论点：让模型写代码而不是写 JSON 工具调用，**少 30% 的步骤**
- **读法**：不要通读，只问一个问题——**"它把 mini-coding-agent 里那些硬编码的部分抽象成了什么接口？"**

### `HKUDS/nanobot`（只在需要时定点查）

- 位置：`D:\python\projectCode\_oss-reference\nanobot\`
- **只读 `session/`（4,059 行）+ `agent/context_governance.py`（892 行）**
- 对照点：mini-coding-agent 的削减是**字符级 clip**，nanobot 是**摘要压缩 + 检查点标记**。前者简单粗暴但确定性强，后者省得多但会丢信息——**这个对比就是一次完整的架构权衡讨论**，也是面试素材。

---

## 第 5 章｜面试问题库

> 每题都是从**这份代码的取舍**导出的，直接可用。

**Q1. Prompt 怎么组织能省钱？**
> 按变化频率分层：静态（角色/规则/工具表/样例）只构建一次放最前，半静态（工作记忆）居中，每轮变化的转录放最后。因为 prompt caching 按前缀匹配，前缀一变后面全部重算。拼接本身不贵，**缓存命中率归零才贵**。

**Q2. 工具结果太长怎么办？**
> 分层削减：单条裁剪（有上限）→ 时间衰减（近期 900 字符，旧的 180）→ 去重 → 总量兜底。最容易错的是**去重的失效**：模型写过文件后，之前读到的内容就过期了，必须让去重缓存失效。截断时还要显式告诉模型被截了多少字符。

**Q3. 工具调用的安全检查顺序？**
> 白名单 → 参数校验 → 重复调用检测 → 风险审批 → 异常兜底。**校验必须在审批前**，非法调用不该弹窗打扰用户。

**Q4. 怎么防止 agent 改坏系统？**
> 三层：路径校验（`samefile` 比 inode，能挡符号链接，字符串前缀挡不住）、风险工具审批门（ask/auto/never 三档）、精确替换（`old_text` 必须恰好出现一次）。

**Q5. 多 agent 委派要注意什么？**
> 四重边界缺一不可：递归深度、工具权限（子 agent 只读 + 从不自动批准）、步数预算、传递的上下文大小。只限深度是最常见的错误。

**Q6. 会话状态怎么设计？**
> 分两轨：全量 transcript 用于恢复和审计，精简 working memory 用于进 prompt。working memory 用固定容量桶 + LRU 更新，其中"任务锚点"只在第一轮写入，用于防止多轮跑偏。

**Q7. 模型输出格式不可靠怎么办？**
> 双格式解析（JSON 工具调用 + XML 风格多行内容），解析失败返回 `retry` 并向上下文注入一条 runtime notice 告诉模型哪里错了；关键是**重试不消耗工具步数预算**，否则模型一胡言乱语就把 agent 卡死。

---

## 附录｜本地资源清单

| 资源 | 路径 | 用途 |
|---|---|---|
| mini-coding-agent | `D:\python\projectCode\mini-coding-agent\` | **主教材**（1019 行 / 916 非空行 + 308 行测试） |
| nanobot | `D:\python\projectCode\_oss-reference\nanobot\` | 定点查上下文/恢复的生产实现 |
| 本文 | `reference/mini-coding-agent导读.md` | 本文件 |
| 源码阅读规划 | [READING_PLAN.md](../READING_PLAN.md) | 5 周计划 + 四句话记录模板 |
| 记录模板 | [notes/源码头测模板.md](../notes/源码头测模板.md) | 每次读完必填 |
