import httpx
import pybreaker
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError
import logging
logging.basicConfig(level=logging.INFO)

breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=10)

# Retry with exponential backoff and jitter
@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=1, max=10))
def call_slow_endpoint():
    response = httpx.get("http://localhost:8000/slow", timeout=5)
    return response.json()

def call_unreliable():
    try:
        @breaker
        def wrapped_call():
            return httpx.get("http://localhost:8000/unreliable", timeout=2).json()
        return wrapped_call()
    except pybreaker.CircuitBreakerError:
        return {"error": "Circuit Breaker is OPEN"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    print("Calling slow with retry:")
    try:
        print(call_slow_endpoint())
    except RetryError:
        print("Retry failed after several attempts")

    print("Calling unreliable with circuit breaker:")
    for _ in range(10):
        print(call_unreliable())