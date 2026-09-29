# -*- coding: utf-8 -*-
# @Author   : WangZZZ
# @Date     : 2026/9/29 22:53
from langchain_deepseek import ChatDeepSeek
import os

from dotenv import load_dotenv

load_dotenv()

deepseek_llm = ChatDeepSeek(
    api_key=os.environ.get("OPENAI_API_KEY"),
    api_base=os.environ.get("OPENAI_BASE_URL"),
    model_name =os.environ.get("MODEL_NAME")
)

print(deepseek_llm.invoke("简洁 请你介绍下你自己"))