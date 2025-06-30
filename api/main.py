from fastapi import FastAPI
import random
import time

app = FastAPI()

@app.get("/healthy")
def healthy():
    return {"status": "healthy"}

@app.get("/unreliable")
def unreliable():
    if random.random() < 0.5:
        return {"status": "success"}
    else:
        raise Exception("Random failure")

@app.get("/slow")
def slow():
    delay = random.randint(1, 10)
    time.sleep(delay)
    return {"status": "success", "delay": delay}