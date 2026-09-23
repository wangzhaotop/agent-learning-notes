import json

# ========== 0. 异常是一棵继承树(和 Java 的 Throwable 家族同构) ==========
# BaseException
#  ├─ KeyboardInterrupt          ← Ctrl+C 就是它,别去接
#  └─ Exception                  ← 你该接住的都是它的子孙
#      ├─ ValueError             ← 值不合法:int("abc")
#      ├─ TypeError              ← 类型不匹配:"a" + 1
#      ├─ KeyError / IndexError  ← 字典没这键 / 列表越界
#      ├─ FileNotFoundError      ← open 一个不存在的文件
#      └─ RuntimeError           ← 运行期错误的兜底父类;自定义异常一般直接继承 Exception


# ========== 1. try / except / else / finally ==========
def safe_div(a,b):
    try:
        result = a / b
    except ZeroDivisionError:  # except = Java 的 catch
        print(f"  捕获除零:{a}/{b}")
        return None
    except TypeError as e:  # as e = catch (ArithmeticException e)
        print(f"  捕获类型错误:{e}")
        return None
    else:  # Java 没有:try 没抛异常才走,成功路径单独放
        print(f"  成功:{a}/{b} = {result}")
        return result
    finally:  # 与 Java 相同:无论如何都执行
        print("  --- 本次计算结束 ---")

safe_div(6, 3)
safe_div(1, 0)
safe_div("a", 2)

# except 要先子类后父类:先写 except Exception 会"截胡"所有异常,
# 后面的具体 except 永远轮不到——和 Java 的 catch 顺序规则一样

# ========== 2. raise = throw;自定义异常 = extends Exception ==========
class ToolError(Exception):
    """工具执行失败——Agent 项目里最常自定义的异常"""


TOOL_IMPLS = {"echo": lambda s: s, "upper": str.upper}


def run_tool(name: str, args: str) -> str:
    if name not in TOOL_IMPLS:
        raise ToolError(f"未知工具:{name}")
    return TOOL_IMPLS[name](args)


try:
    print(" ", run_tool("echo", "hi"))
    print(" ", run_tool("fly", "to the moon"))
except ToolError as e:
    # Agent 铁律:工具炸了程序不能崩——把错误文本作为 tool result 喂回模型,
    # 模型看到报错会自己调整
    print(f"  捕获:{e} → 把这句话作为 tool result 喂回模型")


# ========== 3. 异常链:raise ... from e = Java 的 new X(cause) ==========
def parse_model_output(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"模型没按 JSON 返回:{raw!r}") from e   # 保留完整因果链


try:
    parse_model_output("我说的是人话,不是 JSON")
except RuntimeError as e:
    print(f"  捕获:{e}")
    print(f"  根因:{e.__cause__!r}")


# ========== 4. EAFP:Python 的行事风格 ==========
user = {"name": "WangZZZ"}

# LBYL(Java 常写):先检查再取 —— Look Before You Leap
if "mood" in user:
    print(user["mood"])
else:
    print("  LBYL:没有 mood 字段")

# EAFP(Python 常写):先推门,门锁了再配钥匙
try:
    print(user["mood"])
except KeyError:
    print("  EAFP:没有 mood 字段")

# 但最常用的其实是自带默认值的 API:
print(user.get("mood", "neutral"))