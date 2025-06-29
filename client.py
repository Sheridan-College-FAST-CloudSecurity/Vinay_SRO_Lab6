import requests
import pybreaker
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import time
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Replace with your EC2 instance's public IP
BASE_URL = "http://44.200.216.86:5000"

# Initialize metrics storage
metrics = {
    "circuit_breaker_states": [],
    "unreliable_requests": {"success": 0, "failure": 0},
    "slow_requests": {"success": 0, "failure": 0, "retries": [], "response_times": []}
}

# Circuit Breaker listener to log state changes
class CircuitBreakerListener(pybreaker.CircuitBreakerListener):
    def state_change(self, cb, old_state, new_state):
        logger.info(f"Circuit Breaker state changed from {old_state} to {new_state}")
        metrics["circuit_breaker_states"].append({
            "timestamp": datetime.now().isoformat(),
            "old_state": str(old_state),
            "new_state": str(new_state)
        })

# Initialize Circuit Breaker
breaker = pybreaker.CircuitBreaker(
    fail_max=3,
    reset_timeout=30,
    listeners=[CircuitBreakerListener()]
)

@breaker
def call_unreliable_endpoint():
    """Call the unreliable endpoint with Circuit Breaker."""
    response = requests.get(f"{BASE_URL}/unreliable", timeout=5)
    response.raise_for_status()
    return response.json()

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(requests.exceptions.RequestException),
    before_sleep=lambda retry_state: logger.info(
        f"Retrying slow endpoint (attempt {retry_state.attempt_number}) after {retry_state.idle_for:.2f}s"
    )
)
def call_slow_endpoint():
    """Call the slow endpoint with Retry."""
    start_time = time.time()
    response = requests.get(f"{BASE_URL}/slow", timeout=15)
    response_time = time.time() - start_time
    response.raise_for_status()
    metrics["slow_requests"]["response_times"].append(response_time)
    return response.json()

def main():
    """Test Circuit Breaker and Retry patterns."""
    # Test unreliable endpoint with Circuit Breaker
    logger.info("Starting Circuit Breaker test for /unreliable endpoint")
    for i in range(40):  # Extended to 40 requests to allow reset
        try:
            result = call_unreliable_endpoint()
            metrics["unreliable_requests"]["success"] += 1
            logger.info(f"Unreliable Request {i+1}: Success - {result}")
        except pybreaker.CircuitBreakerError:
            metrics["unreliable_requests"]["failure"] += 1
            logger.error(f"Unreliable Request {i+1}: Circuit breaker open, failing fast")
        except requests.exceptions.RequestException as e:
            metrics["unreliable_requests"]["failure"] += 1
            logger.error(f"Unreliable Request {i+1}: Failed - {str(e)}")
        time.sleep(1)

    # Wait to ensure Circuit Breaker reset
    logger.info("Waiting 35 seconds to observe Circuit Breaker reset")
    time.sleep(35)

    # Test one more request to check reset
    try:
        result = call_unreliable_endpoint()
        metrics["unreliable_requests"]["success"] += 1
        logger.info(f"Unreliable Request (post-reset): Success - {result}")
    except pybreaker.CircuitBreakerError:
        metrics["unreliable_requests"]["failure"] += 1
        logger.error("Unreliable Request (post-reset): Circuit breaker still open")
    except requests.exceptions.RequestException as e:
        metrics["unreliable_requests"]["failure"] += 1
        logger.error(f"Unreliable Request (post-reset): Failed - {str(e)}")

    # Test slow endpoint with Retry
    logger.info("Starting Retry test for /slow endpoint")
    for i in range(5):
        try:
            result = call_slow_endpoint()
            metrics["slow_requests"]["success"] += 1
            logger.info(f"Slow Request {i+1}: Success - {result}")
        except requests.exceptions.RequestException as e:
            metrics["slow_requests"]["failure"] += 1
            logger.error(f"Slow Request {i+1}: Failed - {str(e)}")
            metrics["slow_requests"]["retries"].append(str(e))

    # Save metrics to file
    with open("metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info("Metrics saved to metrics.json")

if __name__ == "__main__":
    main()