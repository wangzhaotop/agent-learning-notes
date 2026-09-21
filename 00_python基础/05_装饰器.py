import functools


def my_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print("调用前")
        result = func(*args, **kwargs)
        print("调用后")
        return result

    return wrapper


@my_decorator
def say(name):
    return f"hello {name}"


print(say("tom"))
print(say.__name__)
print(say.__doc__)



def add(a, b):
    """两数之和"""
    return a + b

print(add.__name__)
print(add.__doc__)
