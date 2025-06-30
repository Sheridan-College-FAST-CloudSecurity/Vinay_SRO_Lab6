from fastapi import FastAPI
import random
import time

app = FastAPI()

# Tier 1 - Critical: Product Info
@app.get("/product-info")
def product_info():
    return {
        "product": "Gaming Laptop",
        "price": "$1200",
        "availability": "In stock"
    }

# Tier 2 - Important: User Reviews
@app.get("/reviews")
def reviews():
    # Simulate 30% chance of failure
    if random.random() < 0.3:
        raise Exception("Reviews service unavailable")
    return {
        "reviews": ["Great product!", "Loved it!", "Highly recommended"]
    }

# Tier 3 - Nice-to-Have: Recommendations
@app.get("/recommendations")
def recommendations():
    # Simulate 70% chance of failure due to load
    if random.random() < 0.7:
        raise Exception("Too much load on recommendations")
    return {
        "recommendations": ["Cooling pad", "Wireless mouse", "External SSD"]
    }

# Optional: System load simulator
@app.get("/system-load")
def system_load():
    load = random.randint(10, 100)
    return {"cpu_load_percent": load}
