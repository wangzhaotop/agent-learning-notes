"""评审循环"""
from pydantic import BaseModel, Field, ValidationError

import llm_client


class Verdict(BaseModel):
    passing: bool = Field(description="是否通过全部评审标准")
    issues: list = Field(description="不通过时逐条列出问题;通过时为空数组")


RUBRIC = ("评审标准:1)有明确的起止日期;2)说明了替代充电方案;"
          "3)留了联系人;4)全文不超过 100 字。")


def generate(feedback=None):
    """生成端: 没有初稿就写初稿,有评审意见就按意见进行修改"""
    if feedback is None:
        messages = [
            {"role": "system", "content": "你是公司行政,负责写全员公告。"},
            {"role": "user", "content": "写一条充电桩停用维护的公告,面向全员。"}
        ]
    else:
        messages = [
            {"role": "system", "content": "你是公司行政,负责写全员公告。"},
            {"role": "user", "content": "写一条充电桩停用维护的公告,面向全员。"},
            {"role": "assistant", "content": feedback["draft"]},
            {"role": "user", "content": f"评审意见:\n{feedback['issues']}\n按意见修改,只输出修改后的公告。"},
        ]

    text, _ = llm_client.chat(messages)
    return text


def evaluate(text):
    raw,_ = llm_client.chat([{"role": "system", "content": f"你是严苛的评审员.{RUBRIC}\n只输出 JSON, 字段定义:\n" \
                                                          f"{Verdict.model_json_schema()}"},
                            {"role": "user", "content": text}], response_format={"type": "json_object"})
    try:
        return Verdict.model_validate_json(raw)
    except ValidationError:
        return Verdict(passing=False, issues=["评审输出不合格,按原意见继续改"])

MAX_ROUNDS = 3
draft,feedback = None,None
for round_i in range(1, MAX_ROUNDS + 1):
    draft = generate(feedback)
    v = evaluate(draft)
    print(f"--- 第{round_i}轮 ---\n{draft}\n评审:{'✅ 通过' if v.passing else v.issues}\n")
    if v.passing:
        break
    feedback = {"draft":draft,"issues":";".join(v.issues)}
else:
    print("(达到最大轮数,带病发布——遗留问题要记录在案!)")

print(llm_client.bill())