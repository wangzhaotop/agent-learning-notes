"""orchestrator.py —— orchestrator-workers 模式的可复用模块。
逻辑住这里(无数字前缀才能被 import);04_orchestrator.py 只是演示壳"""
from pydantic import BaseModel, Field

import llm_client


class Subtask(BaseModel):
    subtasks: list[str] = Field(description="3 到 4 个可独立回答、彼此不重叠的子问题")


def plan(topic):
    """主管:拆任务。 输出任务清单,不是答案"""
    raw, _ = llm_client.chat(
        [
            {
                "role": "system",
                "content": "你是调研主管。把主题拆分成3-4个可独立回答的子问题。"
                           "只输出 JSON：{\"subtasks\":[\"...\"]}"
            },
            {
                "role": "user",
                "content": topic
            }
        ],
        response_format={"type": "json_object"}
    )
    return Subtask.model_validate_json(raw).subtasks


def worker(sub):
    """工人:独立回答一个子问题"""
    reply, _ = llm_client.chat([
        {"role": "system", "content": "你是调研员。简洁回答子问题,分点,150 字内,不知道就说不确定。"},
        {"role": "user", "content": sub},
    ])
    return sub, reply


def synthesize(topic, pairs):
    """汇总:合成报告"""
    material = "\n\n".join(f"【{s}】\n{r}" for s, r in pairs)
    reply, _ = llm_client.chat([
        {"role": "system", "content":
            "你是报告撰写员。综合全部调研材料写短报告:第一句给结论,分节陈述,结尾列遗留问题。"},
        {"role": "user", "content": f"主题:{topic}\n\n{material}"},
    ])
    return reply
