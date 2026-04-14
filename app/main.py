from fastapi import FastAPI

app = FastAPI(title = "My API",  version = "1.0.0")

@app.get("/")
def read_root():
    return { "message" : "Hello james james james"}

@app.get("/ping")
def ping_system():
    return {"status": "success", "detail": "pong!"}