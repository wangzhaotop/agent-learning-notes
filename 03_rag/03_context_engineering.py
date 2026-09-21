import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_BASE_URL")
)

MODEL = os.environ.get("MODEL_NAME")


# 工具函数 估算token总量
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

# ---- 技术 1:窗口管理 · 截断策略(保留最近 N 轮) ----
def truncate_messages(messages, max_turns=5):
    """保留 system 消息 + 最近 N 轮对话(一轮 = user + assistant)"""
    system_msgs = [m for m in messages if m["role"] == "system"]
    conversation = [m for m in messages if m["role"] != "system"]

    #从后往前数N轮 (user/assistant) 成对出现
    recent = conversation[-(max_turns*2):] if len(conversation)>max_turns*2 else conversation
    return system_msgs + recent

# ---- 技术 2:摘要压缩 · 把多轮对话浓缩成一段话 ----
def summarize_conversation(messages):
    """调 LLM 把对话历史摘要成一段话"""
    # 过滤出 user 和 assistant 的对话(跳过 system 和 tool)
    conversaion = [m for m in messages if m["role"] in ["user","assistant"] and m.get("content")]
    if not conversaion:
        return ""

    # 拼接成对话
    dialogue  = "\n".join([f"{m['role']} : {m['content']}" for m in conversaion])

    # 让模型摘要
    summary_prompt = f"""请把以下对话浓缩成 3 句话以内的摘要,保留关键信息:
    {dialogue}
    摘要:"""

    response = client.chat.completions.create(
        messages=[{"role": "user", "content": summary_prompt}],
        model= MODEL
    )
    return response.choices[0].message.content.strip()

# ---- 技术 3:混合策略(摘要 + 最近几轮原文) ----
def hybrid_compress(messages, max_tokens=2000, keep_recent=3):
    """
       1. 如果总 token 数 < max_tokens,直接返回
       2. 否则:把前面的对话摘要成一段话,保留最近 keep_recent 轮原文
       """

    system_msgs = [m for m in messages if m["role"] == "system"]
    conversation = [m for m in messages if m["role"] != "system"]

    total_tokens = count_messages_tokens(messages)

    if total_tokens<max_tokens:
        print(f"总 token 数 {total_tokens} 未超限,无需压缩")
        return messages

    print(f"总 token 数 {total_tokens} 超限,开始混合压缩...")

    #先保留最近n的对话
    recent = conversation[-(keep_recent * 2):] if len(conversation) > keep_recent * 2 else conversation
    older = conversation[:-(keep_recent * 2)] if len(conversation) > keep_recent * 2 else []


    #把更早的对话摘要
    if older:
        summary_text = summarize_conversation(older)
        summary_msg = {"role": "system", "content": f"[对话历史摘要] {summary_text}"}
        compressed = system_msgs + [summary_msg] + recent
    else:
        compressed = system_msgs + recent

    new_tokens = count_messages_tokens(compressed)
    print(f"压缩后 token 数: {new_tokens} (节省 {total_tokens - new_tokens})")
    return compressed


# ---- 模拟一个多轮对话场景 ----
messages = [
    {"role": "system", "content": "你是一个助手"},
    {"role": "user", "content": "Python 是什么?"},
    {"role": "assistant", "content": "Python 是一门解释型、面向对象的编程语言,语法简洁,适合初学者。"},
    {"role": "user", "content": "它有什么特点?"},
    {"role": "assistant", "content": "特点包括:易学易用、库生态丰富、支持多种编程范式、跨平台。"},
    {"role": "user", "content": "能用来做什么?"},
    {"role": "assistant", "content": "常用于 Web 开发(Django/Flask)、数据分析(Pandas/Numpy)、机器学习(TensorFlow/PyTorch)、自动化脚本等。"},
    {"role": "user", "content": "和 Java 比有什么优劣?"},
    {"role": "assistant", "content": "Python 优势:语法简洁、开发速度快、库多;劣势:执行速度慢、不适合高并发场景。Java 优势:性能好、静态类型安全;劣势:代码冗长。"},
    {"role": "user", "content": "现在给我写一个 Hello World"},
    {"role": "assistant", "content": "```python\nprint('Hello World')\n```\n这是 Python 最简单的程序。"},
]

print(f"原始对话: {len(messages)} 条消息, 总 token 数: {count_messages_tokens(messages)}")

# ---- 测试策略 1:截断(保留最近 3 轮) ----
truncated = truncate_messages(messages, max_turns=3)
print(f"\n截断策略(保留最近 3 轮): {len(truncated)} 条消息")
for m in truncated:
    print(f"  {m['role']}: {m['content'][:50]}...")

# ---- 测试策略 2:摘要压缩 ----
summary = summarize_conversation(messages)
print(f"\n摘要压缩结果:\n{summary}")

# ---- 测试策略 3:混合策略(摘要前面 + 保留最近 2 轮) ----
compressed = hybrid_compress(messages, max_tokens=500, keep_recent=2)
print(f"\n混合策略: {len(compressed)} 条消息")
for m in compressed:
    role = m["role"]
    content = m["content"][:80] if m.get("content") else "(无内容)"
    print(f"  {role}: {content}...")

