"""结构化输出:模型返回 Pydantic 对象,校验不过自动重试"""
from pydantic import BaseModel, Field, ValidationError

import llm_client

class Reply(BaseModel):
    """演示用:带意图识别的回答"""
    answer:str = Field(description="对用户问题的简短回答")
    intent:str = Field(description="意图:kb(查公司知识库)/time(时间)/file(文件操作)/chat(闲聊)之一")
    need_search:bool = Field(description="是否需要查询知识库")


def ask_structured(user_text,model_cls,retries=2):
    """带自动重试的结构化调用。返回 (对象 or None, 实际尝试次数)"""
    system = (
        "你是结构化输出器。只输出一个 JSON 对象,不要输出任何其他文字。"
        "字段定义(JSON Schema):\n"
        f"{model_cls.model_json_schema()}"
    )

    messages = [
        {"role":"system","content":system},
        {"role":"system","content":user_text}
    ]

    for attempt in range(retries+1):
        resp = llm_client.chat(messages,response_format ={"type":"json_object"})
        raw = resp.choices[0].message.content
        try:
            print(model_cls.model_validate_json(raw))
            return model_cls.model_validate_json(raw),attempt
        except ValidationError as e:
            bad = e.errors()[0]
            print(f"(第 {attempt + 1} 次不合格:{bad['loc']} {bad['msg']},打回重写)")
            messages.append({"role": "assistant", "content": raw})
            messages.append({"role": "user",
                             "content": "上面的输出不符合 JSON Schema,修正后重新只输出 JSON。"})

    return None, retries


if __name__ == "__main__":
    while True:
        text = input("\n问一句(直接回车退出): ").strip()
        if not text:
            break
        obj, attempt = ask_structured(text, Reply)
        if obj is None:
            print("模型始终不合格,放弃")
            continue
        print(f"回答:{obj.answer}\n意图:{obj.intent} | 需要查库:{obj.need_search} | 尝试 {attempt + 1} 次")