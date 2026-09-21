"""
Agent + RAG 集成:Agent 能调用一个"知识库查询"工具,该工具内部做 RAG(检索 chromadb → rerank → 返回结果)
至少 3 个工具:除了"知识库查询",还要有至少 2 个其他工具(比如阶段 2 的 get_current_time / write_file 等,复用即可)
上下文窗口管理:实现混合策略(摘要 + 保留最近 N 轮),并在每次调 LLM 前检查 token 数是否超限
多轮对话记忆:用户可以连续提问,Agent 记得之前的对话(messages 列表跨轮保留)
/reset 和 /save /load:复用阶段 2 的会话保存恢复逻辑
知识库初始化:程序启动时,读取 knowledge/ 文件夹下的 .txt 文件,切块向量化存入 chromadb
"""
import glob
import json

import os

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime
import chromadb
from sentence_transformers import CrossEncoder

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_BASE_URL")
)
MODEL = os.environ.get("MODEL_NAME")


def estimate_tokens(text):
    """粗略估算:中英文混合,平均 2 字符≈1 token"""
    return len(text) // 2


def count_messages_tokens(messages):
    """统计 messages 列表的总 token 数"""
    total = 0
    for msg in messages:
        if "content" in msg and msg["content"]:
            total += estimate_tokens(msg["content"])

        # tool_calls 也占 token,简化处理:按 JSON 字符串长度估算
        if "tool_calls" in msg and msg["tool_calls"]:
            total += estimate_tokens(str(msg["tool_calls"]))

    return total


def chunk_text(text, source_name):
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []

    for i, para in enumerate(paragraphs):
        chunks.append({
            "text": para,
            "metadata": {
                "source_name": source_name,
                "chunk_id": i
            }
        })

    return chunks


def init_knowledge_base():
    """程序启动时调用一次:读 knowledge/*.txt → 切块 → 存入 chromadb"""
    chroma_client = chromadb.Client()
    # get_or_create:避免重跑时报 collection already exists(第 1 课报错表里那条)
    collection = chroma_client.get_or_create_collection(name="knowledge")

    files = sorted(glob.glob("knowledge/*.txt"))
    if not files:
        raise SystemExit("knowledge/ 文件夹是空的,没有可加载的知识库文档")

    # 所有文档的块先攒到一个列表里， 最后一次性 add
    all_chunks = []
    for filepath in files:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        all_chunks.extend(chunk_text(content, os.path.basename(filepath)))

    collection.add(
        documents=[c["text"] for c in all_chunks],
        metadatas=[c["metadata"] for c in all_chunks],
        ids=[f"chunk_{i}" for i in range(len(all_chunks))]
    )
    print(f"知识库初始化完成:{len(files)} 个文档,共 {collection.count()} 块")
    return collection


def get_current_time():
    """ 获取当前的日期和时间"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S %A")


def write_file(path, content):
    """把文本内容写入指定文件(覆盖原内容)"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    return f"已写入 {path},共 {len(content)} 个字符"


def read_file(path):
    """读取指定文件的全部内容"""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


collection = init_knowledge_base()

reranker = CrossEncoder("BAAI/bge-reranker-base")  # 中文 rerank 模型


def search_knowledge(query: str):
    """检索知识库并返回相关内容"""
    # 1. 向量检索粗筛(取 top-100)
    results = collection.query(
        query_texts=[query],
        n_results=10
    )
    retrieved_docs = results["documents"][0]

    # 2.Rerank 精排(取top-3)
    pairs = [(query, doc) for doc in retrieved_docs]
    scores = reranker.predict(pairs)
    top3_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:3]

    # 拼成返回结果
    answer = "\n\n".join([retrieved_docs[i] for i in top3_indices])
    return f"检索到以下相关内容:\n{answer}"


SAVE_FILE = "chat_history.json"


def save_history(msgs):
    """把整个历史消息写入文件中"""
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(msgs, f, ensure_ascii=False, indent=2)


SYSTEM_PROMPT = "你是一个AI助手 能获取日期和时间、能查rag知识库、能读写文件, 简洁回答"
messages = [{"role": "system", "content": SYSTEM_PROMPT}]
max_steps = 5


def load_history():
    """从文件中恢复历史消息 如果不存在的就返回只带system的新列表"""
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    return [{"role": "system", "content": SYSTEM_PROMPT}]


tools = [
    # ---- 1. 搜索 RAG 知识库 ----
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": "搜索本地知识库，返回与问题最相关的文档片段。当用户询问知识库内的内容、文档、资料时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "要检索的问题或关键词"
                    }
                },
                "required": ["query"]
            }
        }
    },

    # ---- 2. 获取当前日期时间 ----
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取当前的日期和时间。当用户询问现在几点、今天几号、星期几时使用。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },

    # ---- 3. 写文件 ----
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "把文本内容写入指定文件（覆盖原内容）。当用户要求保存、写入、生成文件时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件路径，例如 output/result.txt"
                    },
                    "content": {
                        "type": "string",
                        "description": "要写入文件的文本内容"
                    }
                },
                "required": ["path", "content"]
            }
        }
    },

    # ---- 4. 读文件 ----
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取指定文件的全部内容。当用户要求查看、读取某个文件时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "要读取的文件路径，例如 output/result.txt"
                    }
                },
                "required": ["path"]
            }
        }
    }
]

tools_impls = {
    "search_knowledge": search_knowledge,
    "read_file": read_file,
    "write_file": write_file,
    "get_current_time": get_current_time
}


# 把消息切成轮次 对于tool也得支持
def split_into_turns(messages):
    """把非 system 消息按 user 切分成轮次 , 每轮包含完整的tool 调用组"""
    truns = []
    current = []

    for m in messages:
        if m["role"] == "system":
            continue

        # 到user 表示一轮对话结束
        if m["role"] == "user" and current:
            truns.append(current)
            current = []

        current.append(m)

    if current:
        truns.append(current)

    return truns

# 将tool的消息 进行压缩
def message_to_dialogue(messages):
    lines = []

    for m in messages:
        role = m["role"]

        if role == "user":
            lines.append(f"user:{m.get('content', '')}")

        elif role == "assistant":
            if m.get("content"):
                lines.append(f"assistant:{m.get('content')}")
            if m.get("tool_calls"):
                for tc in m["tool_calls"]:
                    name = tc["function"]["name"]
                    args = tc["function"]["arguments"]
                    lines.append(f"assistant调用工具:{name}({args})")

        elif role == "tool":
            content = m.get("content")
            lines.append(f"tool 返回: {content}")

    return "\n".join(lines)


# ---- 技术 2:摘要压缩 · 把多轮对话浓缩成一段话 ----
def summarize_conversation(dialogue):
    """调用LLM把历史对话摘要成一段话"""
    """接收拼好的对话文本(字符串),让模型摘要成一段话"""
    if not dialogue:
        return ""

    summary_prompt = f"""请把以下对话浓缩成3句话以内的摘要,保留关键信息即可:
    {dialogue}
    摘要:"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": summary_prompt}]
    )

    return response.choices[0].message.content.strip()


# ---- 技术 3:混合策略(摘要 + 最近几轮原文) ----
def hybrid_compress(messages, max_tokens=2000, keep_recent=3):
    """
        1. 如果总 token 数 < max_tokens,直接返回
        2. 否则:把前面的对话摘要成一段话,保留最近 keep_recent 轮原文
        3. 不能将tool相关的消息删除掉
    """

    system_msgs = [m for m in messages if m["role"] == "system"]
    conversation = [m for m in messages if m["role"] != "system"]

    total_tokens = count_messages_tokens(messages)

    if total_tokens < max_tokens:
        print(f"总 token 数 {total_tokens} 未超限,无需压缩")
        return messages

    print(f"总 token 数 {total_tokens} 超限,开始混合压缩...")

    turns = split_into_turns(conversation)

    # 先保留最近n的对话
    recent_turns = turns[-keep_recent:] if len(turns) > keep_recent else turns
    older_turns = turns[:-keep_recent] if len(turns) > keep_recent else []

    recent = [m for turn in recent_turns for m in turn]
    older = [m for turn in older_turns for m in turn]

    # 把更早的对话摘要
    if older:
        dialogue = message_to_dialogue(older)
        summary_text = summarize_conversation(dialogue)
        summary_msg = {"role": "system", "content": f"[对话历史摘要] {summary_text}"}
        compressed = system_msgs + [summary_msg] + recent
    else:
        compressed = system_msgs + recent

    new_tokens = count_messages_tokens(compressed)
    print(f"压缩后 token 数: {new_tokens} (节省 {total_tokens - new_tokens})")
    return compressed


def run_tool_calls(assistant_msg, history):
    for tool_call in assistant_msg.tool_calls:
        name = tool_call.function.name

        try:
            args = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError:
            args = {}

        func = tools_impls.get(name)

        if func is None:
            result = f"错误,不存在名为{name}的工具"
        else:
            try:
                result = func(**args)
            except Exception as e:
                result = f"工具执行出错:{e}"

        print(f"[工具] {name}({args}) -> {result}")

        history.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": str(result)
        })

max_tokens = 2000
keep_recent = 3

def reply_agent(user_input):
    messages.append({"role": "user", "content": user_input})

    for _ in range(max_steps):

        # 调用前先检查

        messages[:] = hybrid_compress(messages, max_tokens, keep_recent)

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools
        )

        msg = response.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))

        if not msg.tool_calls:
            # 表示不同调用工具
            return msg.content
        # 表示工具调用中
        run_tool_calls(msg, messages)

    return "(达到最大步数 强制停止)"


while True:
    try:
        user_input = input("\n你: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\n再见")
        break

    if user_input.lower() == "exit":
        break
    if user_input == "/save":
        save_history(messages)
        print(f"已保存的{SAVE_FILE}")
        continue
    if user_input == "/load":
        messages = load_history()
        print(f"已加载{len(messages)}条消息")
        continue
    if user_input == "/reset":
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        print(f"(对话已清空,当前 {len(messages)} 条消息)")
        continue
    if not user_input:
        continue

    reply = reply_agent(user_input)
    print(f"AI:{reply}")
