"""05_mcp/agent_main.py —— 阶段 4 的 Agent 循环,工具表改成"跨进程发现" """
import json
import os
import sys

import llm_client
from mcp import StdioServerParameters
from mcp_client import MCPToolbox

HERE = os.path.dirname(os.path.abspath(__file__))

SERVERS = {
    "file": StdioServerParameters(
        command=sys.executable, args=[os.path.join(HERE, "file_server.py")]
    ),
    # "kb": StdioServerParameters(
    #     command=sys.executable, args=[os.path.join(HERE, "rag_server.py")]
    # ),
}

SYSTEM_PROMPT = (
    "你是星链公司的内部助手。"
    "规则:凡涉及公司内部制度、流程、设施的问题(考勤假期、报销、IT、研发规范、园区生活等),"
    "必须先调用 kb__search_knowledge 查询,禁止凭记忆回答;查不到就明确说\"资料里没有\"。"
    "其他问题正常回答。保持简洁。"
)

MAX_STEPS = 8
SAVE_FILE = "chat_history.json"


def run_tool_calls(tool_calls, history, toolbox):
    for tc in tool_calls:
        name = tc["function"]["name"]
        try:
            args = json.loads(tc["function"]["arguments"] or "{}")
        except json.JSONDecodeError:
            args = {}
        result = toolbox.call_tool(name, args)
        print(f"[工具]{name}({args}) -> {str(result)[:200]}")
        history.append({"role": "tool", "tool_call_id": tc["id"], "content": str(result)})


def reply(user_input, history, toolbox):
    """阶段 4 的循环逻辑一个字没改,变的只是工具表从哪来"""
    history.append({"role": "user", "content": user_input})
    for _ in range(MAX_STEPS):
        content, tool_calls = llm_client.chat_stream(history, tools=toolbox.get_openai_tools())
        if tool_calls:
            history.append({
                "role": "assistant", "content": content or None, "tool_calls": tool_calls
            })
            run_tool_calls(tool_calls, history, toolbox)
        else:
            history.append({"role": "assistant", "content": content})
            return content

    return "(达到最大步数,强制停止)"


def main():
    with MCPToolbox(SERVERS) as toolbox:
        print("动态发现的工具(代码里一个都没写死):")
        for name in toolbox.tool_names():
            print("  -", name)

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        print("Agent 已启动(exit 退出 /reset /save /load)")
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
                with open(SAVE_FILE, "w", encoding="utf-8") as f:
                    json.dump(messages, f, ensure_ascii=False, indent=2)
                print(f"(已保存到 {SAVE_FILE})")
                continue
            if user_input == "/load":
                if os.path.exists(SAVE_FILE):
                    with open(SAVE_FILE, "r", encoding="utf-8") as f:
                        messages = json.load(f)
                    print(f"(已加载 {len(messages)} 条消息)")
                else:
                    print("(还没有存档)")
                continue
            if not user_input:
                continue
            print(f"AI: {reply(user_input, messages, toolbox)}")


if __name__ == "__main__":
    main()