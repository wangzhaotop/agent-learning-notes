"""薄壳:命令路由 + 对话循环。业务逻辑一行都不该出现在这里"""
import json
import os

from agent import reply
import rag   # noqa: F401  触发 @tool 注册:不 import 这一行,search_knowledge 不会进注册表

SAVE_FILE = "chat_history.json"

# 阶段 3 的教训写进规则:什么时候必须查库、查不到怎么办
SYSTEM_PROMPT = (
    "你是星链公司的内部助手。"
    "规则:凡涉及公司内部制度、流程、设施的问题(考勤假期、报销、IT、研发规范、园区生活等),"
    "必须先调用 search_knowledge 查询,禁止凭记忆回答;查不到就明确说\"资料里没有\"。"
    "其他问题正常回答。保持简洁。"
)
messages = [{"role": "system", "content": SYSTEM_PROMPT}]


def save_history(msgs):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(msgs, f, ensure_ascii=False, indent=2)


def load_history():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    # 没有文件的话 返回系统消息进行兜底
    return [{"role": "system", "content": SYSTEM_PROMPT}]


print(f"Agent 已启动(exit 退出 /reset /save /load)")
while True:
    try:
        user_input = input("\n你: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\n再见")
        break
    if user_input.lower() == "exit":
        break
    if user_input == "/reset":
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        print("(对话已清空)")
        continue
    if user_input == "/save":
        save_history(messages)
        print(f"(已保存到 {SAVE_FILE})")
        continue
    if user_input == "/load":
        messages = load_history()
        print(f"(已加载 {len(messages)} 条消息)")
        continue
    if not user_input:
        continue

    print(f"AI: {reply(user_input, messages)}")
