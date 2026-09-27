"""ReAct:纯提示词驱动的 Agent。对比 function calling 理解协议的价值"""
import json

import llm_client
from tools import TOOL_REGISTRY, call_tool

MAX_STEPS = 6


def build_tool_menu():
    lines = []
    for name, meta in TOOL_REGISTRY.items():
        params = ",".join(meta["params"]["properties"].keys())
        lines.append(f"-{name}({params}):{meta['doc']}")

    return "\n".join(lines)


def parse_action(text):
    """从模型文本里抠出 Action 和 Action Input——ReAct 的脆弱之处就在这"""
    action, action_input = None, {}
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("Action:") and action is None:
            action = line.split("Action:", 1)[1].strip()
        elif line.startswith("Action Input:"):
            try:
                action_input = json.loads(line.split("Action Input:", 1)[1].strip())
            except json.JSONDecodeError:
                action_input = {}
    return action, action_input


def react_reply(user_input, history):
    history.append({"role": "user", "content": user_input})
    system = f"""你是使用工具的助手。严格按以下两种格式之一回答，不要输出别的内容:
    
    Thought: <一句话思考该做什么>
    Action: <工具名,必须是下面菜单之一>
    Action Input: <JSON 对象,是工具参数,没有参数写 {{}}>
    
    或(已经有答案时):
    
    Thought: <一句话思考>
    Final Answer: <给用户的最终回答>     
    
    可用工具菜单:
    {build_tool_menu()}
    """
    history.insert(0, {"role": "system", "content": system})

    for step in range(MAX_STEPS):
        text = llm_client.chat(history).choices[0].message.content
        history.append({"role": "assistant", "content": text})
        print(f"--- 第{step + 1}步 ---\n{text}")

        if "Final Answer:" in text:
            return text.split("Final Answer:", 1)[1].strip()

        action, action_input = parse_action(text)
        if action is None:
            history.append({
                "role": "user",
                "content": "格式不对!必须严格按 Thought/Action/Action Input 或 Final Answer 输出。"
            })
            continue

        result = call_tool(action, action_input)
        print(f"[工具]{action}({action_input}) -> {result}")
        history.append({"role": "user", "content": f"Observation: {result}"})


if __name__ == '__main__':
    history = []
    while True:
        text = input("\n你: ").strip()
        if not text:
            break
        print(f"AI:{react_reply(text, history)}")
