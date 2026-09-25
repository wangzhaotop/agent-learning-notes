"""工具三件套:函数实现 + 给模型看的说明书 + 注册表"""
import inspect
from datetime import datetime

# 注册表:name -> {"func": 函数, "doc": 说明书, "params": JSON Schema}
TOOL_REGISTRY = {}

_TYPE_MAP = {str: "string", int: "integer", float: "number", bool: "boolean"}


def _schema_from_signature(func):
    """反射函数签名 → JSON Schema。有类型注解用注解,没有默认 string"""
    properties, required = {}, []

    for name, parm in inspect.signature(func).parameters.items():
        ann = parm.annotation if parm.annotation is not inspect.Parameter.empty else str
        properties[name] = {"type": _TYPE_MAP.get(ann, "string")}
        if parm.default is inspect.Parameter.empty:
            required.append(name)

    return {"type": "object", "properties": properties, "required": required}


def tool(func):
    """@tool:登记函数、自动生成 Schema。原样返回 func,函数行为不变"""
    TOOL_REGISTRY[func.__name__] = {
        "func": func,
        "doc": inspect.getdoc(func) or "",
        "params": _schema_from_signature(func)
    }

    return func


def get_openai_tools():
    """给 API 的 tools 参数:从注册表拼出协议格式"""
    return [
        {
            "type": "function",
            "function": {
                "name": name,
                "description": meta["doc"],
                "parameters": meta["params"]
            }
        }
        for name, meta in TOOL_REGISTRY.items()
    ]


def call_tool(name, args: dict):
    """统一执行出口:找不到工具、参数解析错、执行报错,全部兜底成字符串"""
    meta = TOOL_REGISTRY.get(name)
    if meta is None:
        return f"错误:不存在名为:{name}的工具"
    try:
        return str(meta["func"](**args))
    except Exception as e:
        return f"工具执行出错:{e}"


@tool
def get_current_time():
    """获取当前的日期和时间"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S %A")


@tool
def write_file(path, content):
    """把文本内容写入指定文件(覆盖原内容)"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"已写入 {path},共 {len(content)} 个字符"

@tool
def read_file(path):
    """读取指定文件的全部内容"""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


