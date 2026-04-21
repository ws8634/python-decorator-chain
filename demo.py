import time
import functools
from typing import Dict, Any, List

from decorators import log, timer, catch, rate_limit, retry, RateLimitExceededError
from chain import DecoratorChain, ChainBuilder, combine, DecoratorPresets


print("=" * 80)
print("【演示 1】单个装饰器的使用 - @log, @timer, @catch, @rate_limit")
print("=" * 80)


@log(level="INFO", log_args=True, log_return=True, log_time=True)
@timer(unit="ms", precision=4)
def normal_business_function(a: int, b: int, name: str = "default") -> Dict[str, Any]:
    """
    正常业务函数 - 执行简单的计算操作
    """
    time.sleep(0.1)
    result = {
        "sum": a + b,
        "product": a * b,
        "name": name.upper(),
        "timestamp": time.time()
    }
    return result


@catch(exceptions=(ValueError, TypeError, ZeroDivisionError), 
       default={"status": "error", "message": "Invalid operation"},
       log_error=True)
@log(level="INFO")
@timer(unit="s", precision=6)
def risky_function(a: float, b: float) -> float:
    """
    有风险的函数 - 可能抛出异常
    """
    if a < 0:
        raise ValueError("参数 a 不能为负数")
    if b == 0:
        raise ZeroDivisionError("除数不能为零")
    time.sleep(0.05)
    return a / b


@rate_limit(max_calls=3, time_window=2.0, wait=False)
@log(level="DEBUG", log_args=False, log_return=True)
@timer(unit="ms", precision=2)
def high_frequency_function(request_id: str) -> Dict[str, Any]:
    """
    高频调用函数 - 用于测试限流
    """
    return {
        "status": "success",
        "request_id": request_id,
        "processed_at": time.time()
    }


print("\n>>> 测试正常业务函数 <<<")
print(f"函数名: {normal_business_function.__name__}")
print(f"函数文档: {normal_business_function.__doc__}")
result1 = normal_business_function(10, 20, name="test_data")
print(f"返回结果: {result1}")


print("\n>>> 测试有风险的函数 - 正常情况 <<<")
result2 = risky_function(10.0, 2.0)
print(f"正常执行结果: {result2}")

print("\n>>> 测试有风险的函数 - 异常情况1 (ZeroDivisionError) <<<")
result3 = risky_function(10.0, 0)
print(f"捕获异常后返回默认值: {result3}")

print("\n>>> 测试有风险的函数 - 异常情况2 (ValueError) <<<")
result4 = risky_function(-5.0, 2.0)
print(f"捕获异常后返回默认值: {result4}")


print("\n>>> 测试高频调用函数 - 限流测试 <<<")
success_count = 0
fail_count = 0

for i in range(5):
    try:
        print(f"\n  第 {i+1} 次调用...")
        result = high_frequency_function(f"req_{i+1}")
        print(f"    成功: {result}")
        success_count += 1
    except RateLimitExceededError as e:
        print(f"    被限流: {e}")
        fail_count += 1

print(f"\n  限流测试结果: 成功={success_count}, 被限流={fail_count}")


print("\n" + "=" * 80)
print("【演示 2】多层装饰器嵌套 - 验证执行顺序和 functools.wraps")
print("=" * 80)


@timer(unit="ms", log_level="INFO")
@catch(exceptions=(Exception,), default="DEMO_DEFAULT")
@log(level="INFO")
def multi_decorated_function(x: int, y: int) -> int:
    """
    多层装饰器装饰的函数
    """
    time.sleep(0.02)
    return x * y


print("\n>>> 验证 functools.wraps 保留原函数信息 <<<")
print(f"函数名: {multi_decorated_function.__name__}")
print(f"函数文档: {multi_decorated_function.__doc__}")
print(f"函数签名信息已保留: {functools.WRAPPER_ASSIGNMENTS}")

print("\n>>> 测试多层装饰器执行 <<<")
result5 = multi_decorated_function(6, 7)
print(f"执行结果: {result5}")


print("\n" + "=" * 80)
print("【演示 3】DecoratorChain 装饰器编排工具类")
print("=" * 80)


def business_service_a(user_id: int, action: str) -> Dict[str, Any]:
    """
    业务服务 A
    """
    time.sleep(0.03)
    return {
        "user_id": user_id,
        "action": action,
        "status": "completed"
    }


def business_service_b(data: List[int]) -> int:
    """
    业务服务 B
    """
    time.sleep(0.01)
    return sum(data)


print("\n>>> 创建自定义装饰器链 <<<")
custom_chain = DecoratorChain()
custom_chain.add(log, level="INFO", log_args=True, log_return=True)
custom_chain.add(timer, unit="ms", precision=3)
custom_chain.add(catch, exceptions=(Exception,), default=None, log_error=True)

print(f"装饰器链: {custom_chain}")
print(f"装饰器数量: {len(custom_chain)}")

print("\n>>> 应用装饰器链到函数 <<<")
decorated_service_a = custom_chain.apply(business_service_a)
decorated_service_b = custom_chain.apply(business_service_b)

print(f"\n  测试 decorated_service_a:")
result6 = decorated_service_a(1001, "login")
print(f"    结果: {result6}")

print(f"\n  测试 decorated_service_b:")
result7 = decorated_service_b([1, 2, 3, 4, 5])
print(f"    结果: {result7}")


print("\n>>> 批量应用装饰器链 <<<")
def func1(): return "func1"
def func2(): return "func2"
def func3(): return "func3"

decorated_funcs = custom_chain.apply_batch(func1, func2, func3)
print(f"批量装饰了 {len(decorated_funcs)} 个函数")

for i, df in enumerate(decorated_funcs):
    print(f"\n  执行 decorated_func_{i+1}:")
    result = df()
    print(f"    结果: {result}")


print("\n>>> 动态修改装饰器链 <<<")
dynamic_chain = DecoratorChain()
dynamic_chain.add(log, level="INFO")
print(f"初始链: {dynamic_chain}")

dynamic_chain.add_before(timer, unit="s")
print(f"添加到前面: {dynamic_chain}")

dynamic_chain.add_after(catch, exceptions=(Exception,), default="ERROR")
print(f"添加到后面: {dynamic_chain}")

dynamic_chain.remove(1)
print(f"移除索引1的装饰器: {dynamic_chain}")

copied_chain = dynamic_chain.copy()
print(f"复制的链: {copied_chain}")


print("\n" + "=" * 80)
print("【演示 4】预定义装饰器链 Presets")
print("=" * 80)

print("\n>>> 使用 logging_chain 预设 <<<")
logging_chain = DecoratorPresets.logging_chain()
print(f"Logging Chain: {logging_chain}")

@logging_chain
def api_call_endpoint(url: str, method: str = "GET") -> Dict[str, Any]:
    time.sleep(0.05)
    return {"url": url, "method": method, "status": 200}

result8 = api_call_endpoint("https://api.example.com/data", "GET")
print(f"API 调用结果: {result8}")


print("\n>>> 使用 safe_execution_chain 预设 <<<")
safe_chain = DecoratorPresets.safe_execution_chain()
print(f"Safe Execution Chain: {safe_chain}")

@safe_chain
def unsafe_operation(x: int, y: int) -> float:
    if x < 0:
        raise ValueError("Negative value not allowed")
    return x / y

result9 = unsafe_operation(-10, 2)
print(f"安全执行结果 (捕获异常): {result9}")


print("\n>>> 使用 api_chain 预设 <<<")
api_chain = DecoratorPresets.api_chain(max_calls=5, time_window=10.0)
print(f"API Chain: {api_chain}")

@api_chain
def public_api(request: Dict[str, Any]) -> Dict[str, Any]:
    return {"data": "sensitive_data", "status": "ok"}

result10 = public_api({"user": "test"})
print(f"API 结果: {result10}")


print("\n" + "=" * 80)
print("【演示 5】@retry 装饰器 - 失败重试机制")
print("=" * 80)

call_counter = 0

@retry(max_attempts=3, delay=0.5, backoff=1.0)
@log(level="INFO")
@timer(unit="ms")
def flaky_service() -> str:
    """
    不稳定的服务 - 模拟间歇性失败
    """
    global call_counter
    call_counter += 1
    
    if call_counter < 3:
        raise ConnectionError(f"Service unavailable (attempt {call_counter})")
    
    return "SUCCESS: Service is now available"


print("\n>>> 测试失败重试机制 <<<")
try:
    result11 = flaky_service()
    print(f"最终结果: {result11}")
except Exception as e:
    print(f"最终失败: {e}")


print("\n" + "=" * 80)
print("【演示 6】完整企业级场景 - 综合所有装饰器")
print("=" * 80)

enterprise_chain = DecoratorChain()
enterprise_chain.add(timer, unit="ms", precision=3)
enterprise_chain.add(catch, exceptions=(RateLimitExceededError, ValueError, Exception), 
                     default={"error": "Service temporarily unavailable"}, log_error=True)
enterprise_chain.add(rate_limit, max_calls=2, time_window=5.0)
enterprise_chain.add(retry, max_attempts=2, delay=0.3, backoff=1.5, exceptions=(ConnectionError,))
enterprise_chain.add(log, level="INFO", log_args=True, log_return=True)

print(f"\n企业级装饰器链: {enterprise_chain}")

enterprise_fail_count = 0

@enterprise_chain
def critical_business_operation(user_id: int, amount: float) -> Dict[str, Any]:
    """
    关键业务操作 - 转账/支付等
    """
    global enterprise_fail_count
    enterprise_fail_count += 1
    
    if enterprise_fail_count < 2:
        raise ConnectionError("Database connection timeout")
    
    if amount <= 0:
        raise ValueError("Invalid amount")
    
    time.sleep(0.1)
    return {
        "transaction_id": f"TXN_{int(time.time())}",
        "user_id": user_id,
        "amount": amount,
        "status": "COMPLETED"
    }


print("\n>>> 测试企业级关键业务操作 <<<")
print(f"\n  测试1: 正常转账 (会先触发重试机制)")
result12 = critical_business_operation(12345, 100.50)
print(f"    结果: {result12}")

print(f"\n  测试2: 无效金额 (异常捕获)")
result13 = critical_business_operation(12345, -50.0)
print(f"    结果: {result13}")

print(f"\n  测试3: 超过限流 (第3次调用)")
result14 = critical_business_operation(12345, 200.0)
print(f"    结果: {result14}")


print("\n" + "=" * 80)
print("演示完成！")
print("=" * 80)

print("""

总结：
1. ✅ 实现了 4 个核心装饰器: @log, @timer, @catch, @rate_limit
2. ✅ 使用 functools.wraps 保留原函数签名、name、doc
3. ✅ 实现了 DecoratorChain 装饰器编排工具类，支持动态组合
4. ✅ 提供了预定义装饰器链 (DecoratorPresets)
5. ✅ 支持多层嵌套，执行顺序正确
6. ✅ 分模块实现: decorators.py, chain.py, demo.py

输出包含:
- 调用记录 (CALL_ID, 函数名, 参数, 返回值)
- 耗时统计 (秒/毫秒/微秒级别)
- 异常捕获和处理日志
- 限流拦截和重试日志

""")
